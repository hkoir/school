from celery import shared_task
from .models import Asset
from django.utils import timezone

@shared_task

from django_tenants.utils import schema_context
from clients.models import Client  # your tenant model
from finance.models import Asset
from celery import shared_task

@shared_task
def depreciate_assets_task():
    for tenant in Client.objects.exclude(schema_name='public'):
        with schema_context(tenant.schema_name):
            for asset in Asset.objects.all():
                asset.apply_asset_depreciation()




