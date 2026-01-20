from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
from .models import HostelAssignment,TransportAssignment,ExamFeeAssignment
from payments.models import HostelRoomPayment,TransportPayment,ExamFeePayment



@receiver(post_save, sender=HostelAssignment)
def create_hostel_payment_placeholders(sender, instance, created, **kwargs):
     if created:  
        enrollment = getattr(instance, 'student_enrollment', None)
        if not enrollment:
            return
        academic_year = getattr(enrollment, 'academic_year', date.today().year)


        for month in range(1, 13): 
            HostelRoomPayment.objects.get_or_create(
                student=instance.student,
                hostel_room=instance.hostel_room,
                hostel_assignment = instance,
                academic_year=academic_year,
                month=month,
                defaults={
                    'total_amount':instance.hostel_room.fee,
                    'amount_paid': 0,
                     'payment_status':'due',
                }
            )


@receiver(post_save, sender=TransportAssignment)
def create_transport_payment_placeholders(sender, instance, created, **kwargs):
    if created:  
        enrollment = getattr(instance, 'student_enrollment', None)
        if not enrollment:
            return
        academic_year = getattr(enrollment, 'academic_year', date.today().year)

        for month in range(1, 13):
            TransportPayment.objects.get_or_create(
                student=instance.student,
                transport_assignment=instance,
                transport_route=instance.route,
                academic_year=academic_year,
                month=month,
                defaults={
                    'due_amount':instance.route.fee,
                    'total_amount':instance.route.fee,
                    'amount_paid': 0,
                      'payment_status':'due',
                }
            )



@receiver(post_save, sender=ExamFeeAssignment) # this assignment is being happening at results app at :create_exam_with_fee
def create_exam_fee_placeholders(sender, instance, created, **kwargs):
    if created and instance.student and instance.exam_fee:
        payment_exists = ExamFeePayment.objects.filter(
            student=instance.student,
            exam_fee=instance.exam_fee
        ).exists()
        if not payment_exists:
            ExamFeePayment.objects.create(
                student=instance.student,
                exam_fee=instance.exam_fee,
                total_amount=instance.exam_fee.amount,
                due_amount=instance.exam_fee.amount,
                amount_paid=0,
                payment_status='due',
                payment_date = None
            )

