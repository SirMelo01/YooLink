import os

from django.conf import settings
from django.core.exceptions import ValidationError


MB = 1024 * 1024

UPLOAD_KIND_IMAGE = "image"
UPLOAD_KIND_VIDEO = "video"
UPLOAD_KIND_DOCUMENT = "document"
UPLOAD_KIND_ARCHIVE = "archive"
UPLOAD_KIND_SUBTITLE = "subtitle"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt"}
ARCHIVE_EXTENSIONS = {".zip"}
SUBTITLE_EXTENSIONS = {".vtt"}
ANYFILE_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS | ARCHIVE_EXTENSIONS

DEFAULT_UPLOAD_LIMIT_BYTES = {
    UPLOAD_KIND_IMAGE: 12 * MB,
    UPLOAD_KIND_VIDEO: 250 * MB,
    UPLOAD_KIND_DOCUMENT: 50 * MB,
    UPLOAD_KIND_ARCHIVE: 100 * MB,
    UPLOAD_KIND_SUBTITLE: 1 * MB,
}


def configured_upload_limits():
    limits = dict(DEFAULT_UPLOAD_LIMIT_BYTES)
    limits.update(getattr(settings, "YCMS_UPLOAD_LIMIT_BYTES", {}) or {})
    return limits


def max_upload_size(upload_kind):
    return configured_upload_limits().get(upload_kind, DEFAULT_UPLOAD_LIMIT_BYTES[UPLOAD_KIND_DOCUMENT])


def format_file_size(size):
    size = int(size or 0)
    if size >= MB:
        mb_value = size / MB
        return f"{mb_value:.0f} MB" if mb_value.is_integer() else f"{mb_value:.1f} MB"
    kb_value = max(1, round(size / 1024))
    return f"{kb_value} KB"


def validation_error_message(error):
    if getattr(error, "messages", None):
        return str(error.messages[0])
    return str(error)


def file_extension(value):
    return os.path.splitext(getattr(value, "name", "") or "")[1].lower()


def validate_extension(value, allowed_extensions, label="Datei"):
    extension = file_extension(value)
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValidationError(f"{label}: Dateiformat \"{extension or 'unbekannt'}\" wird nicht unterstuetzt. Erlaubt: {allowed}.")


def validate_upload_size(value, upload_kind, label="Datei"):
    size = int(getattr(value, "size", 0) or 0)
    max_size = max_upload_size(upload_kind)
    if size > max_size:
        raise ValidationError(
            f"{label} ist zu gross ({format_file_size(size)}). "
            f"Maximal erlaubt: {format_file_size(max_size)}."
        )


def validate_image_upload(value, label="Bild"):
    validate_extension(value, IMAGE_EXTENSIONS, label)
    validate_upload_size(value, UPLOAD_KIND_IMAGE, label)


def validate_video_upload(value, label="Video"):
    validate_extension(value, VIDEO_EXTENSIONS, label)
    validate_upload_size(value, UPLOAD_KIND_VIDEO, label)


def validate_video_thumbnail_upload(value, label="Thumbnail"):
    validate_extension(value, IMAGE_EXTENSIONS - {".gif"}, label)
    validate_upload_size(value, UPLOAD_KIND_IMAGE, label)


def validate_subtitle_upload(value, label="Untertiteldatei"):
    validate_extension(value, SUBTITLE_EXTENSIONS, label)
    validate_upload_size(value, UPLOAD_KIND_SUBTITLE, label)


def anyfile_upload_kind(value):
    extension = file_extension(value)
    if extension in IMAGE_EXTENSIONS:
        return UPLOAD_KIND_IMAGE
    if extension in VIDEO_EXTENSIONS:
        return UPLOAD_KIND_VIDEO
    if extension in ARCHIVE_EXTENSIONS:
        return UPLOAD_KIND_ARCHIVE
    return UPLOAD_KIND_DOCUMENT


def validate_anyfile_upload(value, label="Datei"):
    validate_extension(value, ANYFILE_EXTENSIONS, label)
    validate_upload_size(value, anyfile_upload_kind(value), label)
