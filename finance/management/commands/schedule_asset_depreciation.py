from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class Command(BaseCommand):
    help = "Schedule the monthly asset depreciation task"

    def handle(self, *args, **kwargs):
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",         # 12:00 AM
            day_of_month="1", # On the 1st of every month
            month_of_year="*", 
            day_of_week="*", 
        )

        task_name = "Monthly Asset Depreciation"

        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule,
                name=task_name,
                task="finance.tasks.depreciate_assets_task",  # <-- this must match the dotted path to your task
                kwargs=json.dumps({}),
                one_off=False,
            )
            self.stdout.write(self.style.SUCCESS("✅ Monthly asset depreciation task scheduled successfully!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already scheduled!"))
