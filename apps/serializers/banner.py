from rest_framework import serializers

from apps.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category_id = serializers.CharField(allow_null=True, read_only=True)

    class Meta:
        model = Banner
        fields = ("id", "image_url", "link_type", "link_url", "category_id", "view_count")

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url
