from django.apps import AppConfig


class FakeUberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fake_uber'
