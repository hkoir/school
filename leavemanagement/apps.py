from django.apps import AppConfig


class LeavemanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leavemanagement'


    def ready(self):
        import leavemanagement.signals
