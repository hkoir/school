from django.db import models

from clients.models import Client





class PaymentSystem(models.Model):
    PAYMENT_METHODS = (
        ('bKash', 'bKash'),
        ('Rocket', 'Rocket'),
        ('CreditCard', 'CreditCard'),
        ('PayPal', 'PayPal'),
        ('sslcommerz', 'SSLCommerz'),
    )

    method = models.CharField(max_length=50, choices=PAYMENT_METHODS, unique=True)
    name = models.CharField(max_length=255)
    sandbox_url = models.URLField(blank=True, null=True)
    production_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class TenantPaymentConfig(models.Model):
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE,null=True,blank=True)
    payment_system = models.ForeignKey(PaymentSystem, on_delete=models.CASCADE,null=True,blank=True)    
    is_active = models.BooleanField(default=True)
    is_sandbox = models.BooleanField(default=True)
    
    # Credential and config fields (only the ones tenant-specific)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    client_id = models.CharField(max_length=255, blank=True, null=True)
    client_secret = models.CharField(max_length=255, blank=True, null=True)
    merchant_id = models.CharField(max_length=255, blank=True, null=True)
    store_id = models.CharField(max_length=255, blank=True, null=True)
    store_password = models.CharField(max_length=255, blank=True, null=True)    
    payment_redirect_url = models.URLField(blank=True, null=True)
    extra_config = models.JSONField(blank=True, null=True)

    def get_payment_url(self):
        return self.payment_system.sandbox_url if self.is_sandbox else self.payment_system.production_url

    def __str__(self):
        return f"Payment config for {self.tenant.name} using {self.payment_system.name}"






