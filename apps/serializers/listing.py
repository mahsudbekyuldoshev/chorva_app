from rest_framework import serializers
from rest_framework.fields import SerializerMethodField, ListField, FileField
from rest_framework.serializers import ModelSerializer

from apps.models import Category, Listing, ListingMedia, Favorite, Reel, Report

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
        fields = ('id', 'category', 'title', 'description', 'price', 'currency', 'lat', 'lng', 'address_text', 'expires_at', 'uploaded_files')

    def create(self, validated_data):
        uploaded_files = validated_data.pop('uploaded_files', [])
        listing = Listing.objects.create(user=self.context['request'].user, **validated_data)
        for file in uploaded_files:
            # Simple logic: if ext is mp4/mov etc it's video, else image
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
