from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdmissionFeePolicy, AdmissionFee
from decimal import Decimal


@receiver(post_save, sender=AdmissionFeePolicy)
def update_total_admission_fee(sender, instance, created, **kwargs): 
    if created or instance.total_admission_fee is None:
        total_fee = Decimal(0.00) 
        admission_fees = AdmissionFee.objects.filter(admission_fee_policy=instance)
        for fee in admission_fees:
            total_fee += fee.amount
        instance.total_admission_fee = total_fee
        instance.save(update_fields=['total_admission_fee'])


@receiver(post_save, sender=AdmissionFee)
def update_policy_total_fee(sender, instance, created, **kwargs):
    if instance.admission_fee_policy:
        total_fee = Decimal(0.00)
        admission_fees = AdmissionFee.objects.filter(admission_fee_policy=instance.admission_fee_policy)

        for fee in admission_fees:
            total_fee += fee.amount
        admission_fee_policy = instance.admission_fee_policy
        admission_fee_policy.total_admission_fee = total_fee
        admission_fee_policy.save(update_fields=['total_admission_fee'])
