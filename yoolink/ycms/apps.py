# yoolink/ycms/apps.py
from django.apps import AppConfig

class YcmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "yoolink.ycms"

    def ready(self):
        # Import registriert die Signal-Receiver (Seiteneffekt)
        from . import signals  # noqa: F401  # type: ignore[unused-import]
