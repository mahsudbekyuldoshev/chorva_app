import os
import subprocess
import tempfile

from django.core.files.base import ContentFile

MAX_VIDEO_DURATION_SECONDS = 60
MAX_VIDEO_SIZE_MB = 50
MAX_PHOTO_SIZE_MB = 10


class VideoProcessingError(Exception):
    pass


def _write_to_temp_file(django_file):
    """Django File/UploadedFile obyektini vaqtinchalik faylga yozadi va yo'lini qaytaradi."""
    suffix = os.path.splitext(django_file.name)[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            django_file.seek(0)
        except (AttributeError, ValueError):
            pass
        for chunk in django_file.chunks():
            tmp.write(chunk)
        path = tmp.name
    try:
        django_file.seek(0)
    except (AttributeError, ValueError):
        pass
    return path


def get_video_duration_seconds(django_file) -> float:
    """ffprobe orqali video davomiyligini soniyalarda qaytaradi."""
    path = _write_to_temp_file(django_file)
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", path,
            ],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise VideoProcessingError(f"ffprobe xatosi: {result.stderr.strip()}")
        return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as exc:
        raise VideoProcessingError(str(exc)) from exc
    finally:
        os.unlink(path)


def generate_thumbnail_file(django_file):
    """Videodan birinchi kadrni JPEG sifatida ajratib, ContentFile qaytaradi."""
    video_path = _write_to_temp_file(django_file)
    thumb_path = video_path + "_thumb.jpg"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", thumb_path],
            capture_output=True, timeout=20, check=False,
        )
        if result.returncode != 0 or not os.path.exists(thumb_path):
            raise VideoProcessingError(f"ffmpeg thumbnail xatosi: {result.stderr.decode(errors='ignore')}")
        with open(thumb_path, "rb") as f:
            content = f.read()
        return ContentFile(content, name="thumbnail.jpg")
    except subprocess.TimeoutExpired as exc:
        raise VideoProcessingError(str(exc)) from exc
    finally:
        os.unlink(video_path)
        if os.path.exists(thumb_path):
            os.unlink(thumb_path)
