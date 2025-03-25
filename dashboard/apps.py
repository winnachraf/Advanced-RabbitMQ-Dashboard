from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        """
        Import signals when the app is ready
        """
        import dashboard.signals  # Import signals module to register handlers