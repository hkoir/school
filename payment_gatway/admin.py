from django.contrib import admin

from.models import PaymentSystem,TenantPaymentConfig

admin.site.register(PaymentSystem)
admin.site.register(TenantPaymentConfig)
