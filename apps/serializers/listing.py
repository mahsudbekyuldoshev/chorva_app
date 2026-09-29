from rest_framework import serializers
from rest_framework.fields import FileField, ListField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, ValidationError

from apps.models import Category, Favorite, Listing, ListingMedia, Reel, Report
from apps.utils.media import (
    MAX_PHOTO_SIZE_MB,
    MAX_VIDEO_DURATION_SECONDS,
    MAX_VIDEO_SIZE_MB,
    VideoProcessingError,
    generate_thumbnail_file,
    get_video_duration_seconds,
)

VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')


def is_video_file(filename: str) -> bool:
    return filename.lower().endswith(VIDEO_EXTENSIONS)


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name_uz', 'name_ru', 'name_en', 'icon', 'sort_order')


class ListingMediaSerializer(ModelSerializer):
    class Meta:
        model = ListingMedia
        fields = ('id', 'media_type', 'file', 'thumbnail', 'sort_order')


class ListingListSerializer(ModelSerializer):
    media = ListingMediaSerializer(many=True, read_only=True)
    is_favorite = SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            'id', 'title', 'price', 'currency', 'status', 'listing_type',
            'lat', 'lng', 'media', 'is_favorite', 'created_at'
        )

    def get_is_favorite(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, listing=obj).exists()
        return False


class ListingDetailSerializer(ModelSerializer):
    media = ListingMediaSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    is_favorite = SerializerMethodField()
    user = SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            'id', 'user', 'category', 'title', 'description', 'price',
            'currency', 'status', 'listing_type', 'lat', 'lng', 'address_text',
            'view_count', 'media', 'is_favorite', 'created_at', 'expires_at'
        )

    def get_is_favorite(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, listing=obj).exists()
        return False

    def get_user(self, obj):
        from .user import UserPublicSerializer
        return UserPublicSerializer(obj.user).data


class ListingCreateSerializer(ModelSerializer):
    uploaded_files = ListField(
        child=FileField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    media_keys = ListField(
        child=serializers.CharField(max_length=500),
        write_only=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._downloaded_media = {}

    class Meta:
        model = Listing
        fields = (
            'id', 'category', 'title', 'description', 'price', 'currency',
            'lat', 'lng', 'address_text', 'uploaded_files', 'media_keys'
        )

    def validate_uploaded_files(self, value):
        for f in value:
            size_mb = f.size / (1024 * 1024)
            if is_video_file(f.name):
                if size_mb > MAX_VIDEO_SIZE_MB:
                    raise serializers.ValidationError(
                        f"Video hajmi {MAX_VIDEO_SIZE_MB}MB dan oshmasligi kerak."
                    )
                try:
                    duration = get_video_duration_seconds(f)
                except VideoProcessingError:
                    raise serializers.ValidationError(
                        "Video faylni tahlil qilib bo'lmadi — fayl buzilgan bo'lishi mumkin."
                    )
                if duration > MAX_VIDEO_DURATION_SECONDS:
                    raise serializers.ValidationError(
                        f"Video davomiyligi {MAX_VIDEO_DURATION_SECONDS} soniyadan oshmasligi kerak."
                    )
            else:
                if size_mb > MAX_PHOTO_SIZE_MB:
                    raise serializers.ValidationError(
                        f"Rasm hajmi {MAX_PHOTO_SIZE_MB}MB dan oshmasligi kerak."
                    )
        return value

    def validate_media_keys(self, value):
        from apps.utils.storage import delete_from_minio, download_from_minio
        self._downloaded_media = {}
        for key in value:
            try:
                f = download_from_minio(key)
            except ValueError as exc:
                delete_from_minio(key)
                raise serializers.ValidationError(str(exc))

            size_mb = f.size / (1024 * 1024)
            media_type = 'video' if is_video_file(key) else 'image'
            if media_type == 'video':
                if size_mb > MAX_VIDEO_SIZE_MB:
                    delete_from_minio(key)
                    raise serializers.ValidationError(
                        f"Video hajmi {MAX_VIDEO_SIZE_MB}MB dan oshmasligi kerak."
                    )
                try:
                    duration = get_video_duration_seconds(f)
                except VideoProcessingError:
                    delete_from_minio(key)
                    raise serializers.ValidationError(
                        "Video faylni tahlil qilib bo'lmadi — fayl buzilgan bo'lishi mumkin."
                    )
                if duration > MAX_VIDEO_DURATION_SECONDS:
                    delete_from_minio(key)
                    raise serializers.ValidationError(
                        f"Video davomiyligi {MAX_VIDEO_DURATION_SECONDS} soniyadan oshmasligi kerak."
                    )
            else:
                if size_mb > MAX_PHOTO_SIZE_MB:
                    delete_from_minio(key)
                    raise serializers.ValidationError(
                        f"Rasm hajmi {MAX_PHOTO_SIZE_MB}MB dan oshmasligi kerak."
                    )
            self._downloaded_media[key] = (f, media_type)
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        uploaded_files = attrs.get('uploaded_files', [])
        media_keys = attrs.get('media_keys', [])

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return attrs

        plan = request.user.current_plan
        if not plan:
            return attrs

        total_photos = sum(1 for f in uploaded_files if not is_video_file(f.name)) + \
                       sum(1 for k in media_keys if not is_video_file(k))
        total_videos = sum(1 for f in uploaded_files if is_video_file(f.name)) + \
                       sum(1 for k in media_keys if is_video_file(k))

        existing_photos = 0
        existing_videos = 0
        if self.instance:
            existing_photos = self.instance.media.filter(media_type='image').count()
            existing_videos = self.instance.media.filter(media_type='video').count()

        if existing_photos + total_photos > plan.max_photos_per_listing:
            raise serializers.ValidationError(
                f"Tarifingiz bo'yicha e'lon uchun maksimal {plan.max_photos_per_listing} "
                "ta rasm yuklash mumkin."
            )
        if existing_videos + total_videos > plan.max_videos_per_listing:
            raise serializers.ValidationError(
                f"Tarifingiz bo'yicha e'lon uchun maksimal {plan.max_videos_per_listing} "
                "ta video yuklash mumkin."
            )
        return attrs

    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        media_keys = validated_data.pop('media_keys', [])
        listing = Listing.objects.create(**validated_data)

        sort_order = 0
        for file in uploaded_files:
            media_type = 'video' if is_video_file(file.name) else 'image'
            ListingMedia.objects.create(
                listing=listing, file=file, media_type=media_type, sort_order=sort_order
            )
            sort_order += 1

        for key in media_keys:
            media_type = self._downloaded_media.get(key, (None, 'image'))[1]
            media_obj = ListingMedia(
                listing=listing, media_type=media_type, sort_order=sort_order
            )
            media_obj.file.name = key
            media_obj.save()
            sort_order += 1

        return listing


class FavoriteSerializer(ModelSerializer):
    listing = ListingListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'listing', 'created_at')


class ReelSerializer(ModelSerializer):
    user = SerializerMethodField()
    video_key = serializers.CharField(max_length=500, write_only=True, required=False)
    video = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Reel
        fields = ('id', 'user', 'listing', 'video', 'video_key', 'caption', 'view_count', 'thumbnail', 'created_at')
        read_only_fields = ('thumbnail',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._downloaded_video = None

    def get_user(self, obj):
        from .user import UserPublicSerializer
        return UserPublicSerializer(obj.user).data

    def validate(self, attrs):
        video = attrs.get('video')
        video_key = attrs.get('video_key')

        if (not video and not video_key) or (video and video_key):
            raise serializers.ValidationError("video yoki video_key dan faqat bittasi berilishi kerak.")

        if video_key:
            from apps.utils.storage import delete_from_minio, download_from_minio
            try:
                f = download_from_minio(video_key)
            except ValueError as exc:
                delete_from_minio(video_key)
                raise serializers.ValidationError(str(exc))

            size_mb = f.size / (1024 * 1024)
            if size_mb > MAX_VIDEO_SIZE_MB:
                delete_from_minio(video_key)
                raise serializers.ValidationError(
                    f"Video hajmi {MAX_VIDEO_SIZE_MB}MB dan oshmasligi kerak."
                )
            try:
                duration = get_video_duration_seconds(f)
            except VideoProcessingError:
                delete_from_minio(video_key)
                raise serializers.ValidationError(
                    "Video faylni tahlil qilib bo'lmadi — fayl buzilgan bo'lishi mumkin."
                )
            if duration > MAX_VIDEO_DURATION_SECONDS:
                delete_from_minio(video_key)
                raise serializers.ValidationError(
                    f"Video davomiyligi {MAX_VIDEO_DURATION_SECONDS} soniyadan oshmasligi kerak."
                )
            self._downloaded_video = f

        return attrs

    def create(self, validated_data):
        video_key = validated_data.pop('video_key', None)
        if video_key:
            validated_data.pop('video', None)
            instance = super().create(validated_data)
            instance.video.name = video_key
            instance.save(update_fields=['video'])
        else:
            instance = super().create(validated_data)

        try:
            thumbnail_file = generate_thumbnail_file(instance.video)
            instance.thumbnail.save(thumbnail_file.name, thumbnail_file, save=True)
        except (VideoProcessingError, OSError):
            pass
        return instance


class ReportSerializer(ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'reason', 'comment', 'target_user', 'target_listing')

    def validate(self, attrs):
        if not attrs.get('target_user') and not attrs.get('target_listing'):
            raise ValidationError("Target user or target listing must be provided.")
        return attrs
