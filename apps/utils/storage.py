import uuid

import boto3
from django.conf import settings

ALLOWED_KINDS = {
    "image": (".jpg", ".jpeg", ".png", ".webp"),
    "video": (".mp4", ".mov", ".avi"),
}


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT_URL,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
    )


def generate_presigned_upload(kind: str, ext: str):
    ext = ext.lower().lstrip(".")
    ext_with_dot = f".{ext}"
    if kind not in ALLOWED_KINDS or ext_with_dot not in ALLOWED_KINDS[kind]:
        raise ValueError(
            f"'{kind}' turi uchun '.{ext}' kengaytmasi qo'llab-quvvatlanmaydi."
        )

    key = f"{kind}s/{uuid.uuid4().hex}.{ext}"
    client = _get_s3_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.MINIO_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.MINIO_PRESIGN_EXPIRES_SECONDS,
    )
    public_url = f"{settings.MINIO_PUBLIC_BASE_URL.rstrip('/')}/{key}"
    return upload_url, public_url
