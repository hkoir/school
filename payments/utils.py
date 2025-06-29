
from datetime import date
from payments.models import Payment
from decimal import Decimal
from django.db.models import Sum



def get_total_due_till_today(academic_year, student):
    today = date.today()
    current_month = today.month
    enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
    if not enrollment or not enrollment.feestructure or not enrollment.feestructure.admissionfee_policy:
        return Decimal(0.00)       

    monthly_fee_due = enrollment.feestructure.monthly_tuition_fee * current_month

    total_admission_fee = Decimal(0.00)        

    for fee in enrollment.feestructure.admissionfee_policy.admission_fees.all():
        if fee.due_date.month <= current_month: 
            total_admission_fee += fee.amount

    return monthly_fee_due + total_admission_fee


def get_total_paid_till_today(academic_year, student):
    payments = Payment.objects.filter(academic_year=academic_year, student=student)
    tuition_total = payments.aggregate(total=Sum('monthly_tuition_fee_paid'))['total'] or Decimal(0.00)
    admission_total = payments.aggregate(total=Sum('admission_fee_paid'))['total'] or Decimal(0.00)

    return tuition_total + admission_total


def get_remaining_due_till_today(academic_year, student):
    total_due = get_total_due_till_today(academic_year, student)
    total_paid = get_total_paid_till_today(academic_year, student)       
    return max(total_due - total_paid, Decimal(0.00))
