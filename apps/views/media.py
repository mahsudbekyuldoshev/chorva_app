from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.serializers.media import MediaPresignSerializer
from apps.utils.storage import generate_presigned_upload


@extend_schema(summary="Media yuklash uchun presigned URL olish", tags=["Media"])
class MediaPresignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MediaPresignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            upload_url, public_url = generate_presigned_upload(
                serializer.validated_data["kind"], serializer.validated_data["ext"]
            )
        except ValueError as exc:
            raise ValidationError(str(exc))

        return Response({"upload_url": upload_url, "public_url": public_url})
