from rest_framework import serializers


class MediaPresignSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["image", "video"])
    ext = serializers.CharField(max_length=10)
