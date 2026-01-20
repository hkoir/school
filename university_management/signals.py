from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import calculate_cgpa 

from .models import (
    UniversityPayment, UniversityTermInvoice, StudentTermRegistration,
    StudentTermResult, StudentCGPA,UniversityPayment
    )


from django.db.models import Sum

@receiver(post_save, sender=UniversityPayment)
def update_invoice_and_term_registration(sender, instance, **kwargs):
    invoice = instance.invoice
    agg = invoice.payments.aggregate(
        tuition=Sum('tuition_paid'),
        admission=Sum('admission_paid')
    )

    total_paid = (agg['tuition'] or 0) + (agg['admission'] or 0)

    invoice.total_paid = total_paid
    invoice.due_amount = invoice.total_payable - total_paid

    if invoice.due_amount <= 0:
        invoice.status = 'paid'
    elif total_paid > 0:
        invoice.status = 'partial'
    else:
        invoice.status = 'unpaid'

    invoice.save(update_fields=['total_paid', 'due_amount', 'status'])

    try:
        term_registration = StudentTermRegistration.objects.get(
            enrollment__student=invoice.student,
            term=invoice.term,
            enrollment__program=invoice.program
        )
        term_registration.is_fee_cleared = invoice.due_amount <= 0
        term_registration.is_exam_eligible = term_registration.is_fee_cleared
        term_registration.save()
    except StudentTermRegistration.DoesNotExist:
        pass


from .models import StudentSubjectResult, StudentTermResult, StudentCGPA
from.utils import calculate_term_gpa,calculate_cgpa

@receiver(post_save, sender=StudentSubjectResult)
def update_gpa_and_cgpa(sender, instance, created, **kwargs):
    if not instance.is_published:
        return      
    student = instance.student
    term = instance.term
    session = instance.academic_session

    term_gpa, total_credits = calculate_term_gpa(student, term, session)

    term_result, _ = StudentTermResult.objects.update_or_create(
        student=student,
        academic_session=session,
        term=term,
        defaults={
            "program": instance.program,
            "level": term.level,
            "total_credits": total_credits,
            "gpa": term_gpa,
            "is_published": True,
        }
    )

    cgpa, earned_credits = calculate_cgpa(student)

    StudentCGPA.objects.update_or_create(
        student=student,
        academic_session=session,
        defaults={
            "total_credits": earned_credits,
            "cgpa": cgpa,
        }
    )
