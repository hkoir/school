from .models import AdmissionFeePolicy, AdmissionFee
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from decimal import Decimal
from django.utils import timezone

from students.models import (
    StudentEnrollment,TuitionFeeAssignment,AdmissionFeeAssignment
    
    )
from payments.models import (
   TuitionFeePayment,AdmissionFeePayment, AdmissionFee
    
    )

from django.db import transaction

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




@receiver(post_save, sender=StudentEnrollment)
def on_student_enrollment_created(sender, instance, created, **kwargs):
    if not created:
        return
    student = instance.student
    academic_year = instance.academic_year   
    academic_class = instance.academic_class 
    fee_structure = instance.feestructure

    
    with transaction.atomic():
        if fee_structure:
            tuition_assignment, _ = TuitionFeeAssignment.objects.get_or_create(
                student=student,
                student_enrollment=instance,
                fee_structure=fee_structure,
            )
            for month in range(1, 13):
                TuitionFeePayment.objects.get_or_create(
                    student=student,                
                    tuition_fee_assignment=tuition_assignment,
                    fee_structure=fee_structure,
                    academic_year=academic_year,
                    month=month,
                    defaults={
                        'total_amount': fee_structure.monthly_tuition_fee,
                        'due_amount': fee_structure.monthly_tuition_fee,
                        'amount_paid': 0,
                        'payment_status': 'due',
                    }
                )

        admission_fees = AdmissionFee.objects.filter(
            admission_fee_policy__student_class=instance.academic_class,
            admission_fee_policy__academic_year=instance.academic_year,
            admission_fee_policy__language_version = instance.language
        )
        
        for fee in admission_fees:    
            if not fee.due_month:
                continue  

            admission_assignment, _ = AdmissionFeeAssignment.objects.get_or_create(
                student=student,
                student_enrollment=instance,
                admission_fee=fee,
                defaults={
                    'start_date': date.today(),
                    'is_active': True
                }
            )
           
            AdmissionFeePayment.objects.get_or_create(
                admission_fee_assignment=admission_assignment,
                defaults={
                    'student': student,
                    'fee_structure': fee_structure,
                    'academic_year': academic_year,
                    'month': fee.due_month,   # ✅ user-defined
                    'total_amount': fee.amount,
                    'due_amount': fee.amount,
                    'amount_paid': 0,
                    'payment_status': 'due',
                }
            )



