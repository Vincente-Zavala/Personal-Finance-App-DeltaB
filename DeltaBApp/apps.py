from django.apps import AppConfig


class DeltaBConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "DeltaB"

    def ready(self):
        import DeltaBApp.signals