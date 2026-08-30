from rest_framework.fields import FileField, ListField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, ValidationError

from apps.models import Category, Favorite, Listing, ListingMedia, Reel, Report


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
        fields = ('id', 'title', 'price', 'currency', 'status', 'listing_type', 'lat', 'lng', 'media', 'is_favorite', 'created_at')

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
        fields = ('id', 'user', 'category', 'title', 'description', 'price', 'currency', 'status', 'listing_type', 'lat', 'lng', 'address_text', 'view_count', 'media', 'is_favorite', 'created_at', 'expires_at')

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

    class Meta:
        model = Listing
        fields = ('id', 'category', 'title', 'description', 'price', 'currency', 'lat', 'lng', 'address_text', 'uploaded_files')

    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        # 'user' is passed in perform_create in the view, so do not pass it here.
        # But wait, self.context['request'].user is already here.
        # Let's fix the view's perform_create or this create method.
        # The serializer should NOT be creating the user if it's already in validated_data or handled.
        # In the current implementation: perform_create passes 'user' to save(), which passes it to create().
        # So validated_data already has 'user'.
        listing = Listing.objects.create(**validated_data)
        for file in uploaded_files:
            media_type = 'image'
            if file.name.lower().endswith(('.mp4', '.mov', '.avi')):
                media_type = 'video'
            ListingMedia.objects.create(listing=listing, file=file, media_type=media_type)
        return listing

class FavoriteSerializer(ModelSerializer):
    listing = ListingListSerializer(read_only=True)
    class Meta:
        model = Favorite
        fields = ('id', 'listing', 'created_at')

class ReelSerializer(ModelSerializer):
    user = SerializerMethodField()
    class Meta:
        model = Reel
        fields = ('id', 'user', 'listing', 'video', 'caption', 'view_count', 'created_at')

    def get_user(self, obj):
        from .user import UserPublicSerializer
        return UserPublicSerializer(obj.user).data

class ReportSerializer(ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'reason', 'comment', 'target_user', 'target_listing')
    
    def validate(self, attrs):
        if not attrs.get('target_user') and not attrs.get('target_listing'):
            raise ValidationError("Target user or target listing must be provided.")
        return attrs
