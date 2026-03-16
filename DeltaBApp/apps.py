from django.apps import AppConfig


class DeltaBAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "DeltaBApp"

    def ready(self):
        import DeltaBApp.demo_signals # noqa: F401