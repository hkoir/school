

from datetime import date
from payments.models import Payment
from decimal import Decimal
from django.db.models import Sum

def get_remaining_due_till_today(academic_year, student):
    from datetime import date
    enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
    if not enrollment or not enrollment.feestructure:
        return Decimal(0.00)

    current_month = date.today().month
    monthly_fee = enrollment.feestructure.monthly_tuition_fee
    total_expected = Decimal(monthly_fee) * current_month

    payments = Payment.objects.filter(student=student, academic_year=academic_year)
    total_paid = sum((p.monthly_tuition_fee_paid or 0) for p in payments)

    return max(total_expected - Decimal(total_paid), Decimal(0.00))


def get_total_admission_fee_due_till_today(academic_year, student):
    enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
    if not enrollment or not enrollment.feestructure or not enrollment.feestructure.admissionfee_policy:
        return Decimal(0.00)

    total_fee = sum(fee.amount for fee in enrollment.feestructure.admissionfee_policy.admission_fees.all())
    total_paid = sum((p.admission_fee_paid or 0) for p in 
                     Payment.objects.filter(student=student, academic_year=academic_year))

    return max(Decimal(total_fee) - Decimal(total_paid), Decimal(0.00))







from django.utils.timezone import now
from .models import PaymentInvoice



def create_payment_invoice(payments, invoice_type=None, payment_method=None, entered_amount=None):
    if not payments:
        return None 

    first_payment = payments[0]
    student = getattr(first_payment, 'student', None)
    if not student:
        raise ValueError("Student not found in payment instance.")

    student_enrollment = getattr(student, 'enrolled_students', None)
    student_enrollment = student_enrollment.first() if student_enrollment else None

    total_amount = sum(Decimal(getattr(p, 'total_amount', 0) or 0) for p in payments)
    total_paid = sum(Decimal(getattr(p, 'amount_paid', 0) or 0) for p in payments)
    total_due = sum(Decimal(getattr(p, 'due_amount', 0) or 0) for p in payments)
  
    if entered_amount and entered_amount < total_paid:
        total_paid = Decimal(entered_amount)
        total_due = total_amount - total_paid if total_amount > total_paid else Decimal('0.00')
 
    invoice = PaymentInvoice.objects.create(
        invoice_type=", ".join(invoice_type) if isinstance(invoice_type, list) else invoice_type,
        student=student,
        student_enrollment=student_enrollment,
        amount=total_amount,
        paid_amount=total_paid,
        due_amount=total_due,
        payment_method=payment_method,
        description=f"{', '.join(invoice_type).title() if isinstance(invoice_type, list) else str(invoice_type).title()} payment for {now().strftime('%B %Y')}",
    )

    # Prepare lists to store applied payments for each type
    tuition_payments = []
    admission_payments = []
    hostel_payments = []
    transport_payments = []
    exam_payments = []
    other_payments = []

    for p in payments:
        # Set invoice-level assignment fields if not set already
        if hasattr(p, 'tuition_fee_assignment') and p.tuition_fee_assignment:
            invoice.tution_payment_assignment = p.tuition_fee_assignment
            tuition_payments.append(p)
        elif hasattr(p, 'admission_fee_assignment') and p.admission_fee_assignment:
            invoice.admission_fee_payment_assignment = p.admission_fee_assignment
            admission_payments.append(p)
        elif hasattr(p, 'hostel_assignment') and p.hostel_assignment:
            invoice.hostel_assignment = p.hostel_assignment
            hostel_payments.append(p)
        elif hasattr(p, 'transport_assignment') and p.transport_assignment:
            invoice.transport_assignment = p.transport_assignment
            transport_payments.append(p)
        elif hasattr(p, 'exam_fee_assignment') and p.exam_fee_assignment:
            invoice.exam_fee_assignment = getattr(p.exam_fee_assignment, 'exam_fee_assignment', None)
            exam_payments.append(p)
        elif hasattr(p, 'other_fee_assignment') and p.other_fee:
            invoice.other_fee_assignment = p.other_fee
            other_payments.append(p)

    invoice.save()

    # Set ManyToMany relationships
    if tuition_payments:
        invoice.tuition_payments.set(tuition_payments)
    if admission_payments:
        invoice.admission_payments.set(admission_payments)
    if hostel_payments:
        invoice.hostel_payments.set(hostel_payments)
    if transport_payments:
        invoice.transport_payments.set(transport_payments)
    if exam_payments:
        invoice.exam_payments.set(exam_payments)
    if other_payments:
        invoice.other_payments.set(other_payments)

    return invoice




from django.db.models import Sum
from datetime import date
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render,redirect


def get_due_till_today(student):
    if not student:
        return redirect('students:create_student')

    dues = {}
    today = date.today()
    current_month = today.month
    if today.day < 25:
        due_month = current_month - 1
    else:
        due_month = current_month
    due_month = max(due_month, 1)



    tuition_qs = student.student_tuition_payments.filter(
        academic_year=today.year,    
        month__lte=due_month       
    )
    tuition_expected = tuition_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    tuition_paid = tuition_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0

    dues['tuition'] = {
        'expected': tuition_expected,
        'paid': tuition_paid,
        'net_due': max(tuition_expected - tuition_paid, 0),
        'student':student
    }
  
    admission_qs = student.student_admission_payments.filter(
        academic_year=today.year,
        month__lte=due_month
       
    )
    admission_expected = admission_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    admission_paid = admission_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
   
    dues['admission'] = {
        'expected': admission_expected ,
        'paid': admission_paid,
        'net_due': max(admission_expected - admission_paid, 0),
        'student':student
    }

    hostel_qs = student.student_hostel_payments.filter(
        academic_year=today.year,
        month__lte=due_month
    )
    hostel_expected = hostel_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    hostel_paid = hostel_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
    dues['hostel'] = {
        'expected': hostel_expected ,
        'paid': hostel_paid,
        'net_due': max(hostel_expected - hostel_paid, 0),
         'student':student
    }
    

    transport_qs = student.student_transport_payments.filter(
        academic_year=today.year,
        month__lte=due_month
    )
    transport_expected = transport_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    transport_paid = transport_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0

    
   
    dues['transport'] = {
        'expected': transport_expected ,
        'paid': transport_paid,
        'net_due': max(transport_expected - transport_paid, 0),
         'student':student
    }

 
    exam_qs = student.student_exam_fee_payments.filter(
        academic_year=today.year
    )
    exam_expected = exam_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    exam_paid = exam_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
    dues['exam'] = {
        'expected': exam_expected ,
        'paid': exam_paid,
        'net_due': max(exam_expected - exam_paid, 0),
         'student':student
    }


    other_qs = student.other_fee_students.filter(
        academic_year=today.year
    )
    other_expected = other_qs.aggregate(
        expected=Sum('total_amount')
    )['expected'] or 0
    other_paid = other_qs.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
  
    dues['other'] = {
        'expected': other_expected ,
        'paid': other_paid,
        'net_due': max(other_expected - other_paid, 0),
        'student':student
    }


    return dues





def apply_payment_to_oldest_months(student, payment_type, paid_amount):
    today = date.today()
    updated_records = []
    qs_map = {
        'hostel': student.student_hostel_payments,
        'transport': student.student_transport_payments,
        'tuition': student.student_tuition_payments,
        'admission': student.student_admission_payments,
    }

    due_payments = qs_map.get(payment_type, None)
    if not due_payments:
        return paid_amount, updated_records

    due_payments = due_payments.filter(
        academic_year=today.year,
        month__lte=today.month,
        due_amount__gt=0
    ).order_by('month')

    remaining_amount = paid_amount

    for p in due_payments:
        if remaining_amount <= 0:
            break

        due = p.due_amount or 0
        pay_now = min(due, remaining_amount)
        p.amount_paid += pay_now
        p.due_amount = due - pay_now
        p.payment_status = 'paid' if p.due_amount <= 0 else 'partial'
        p.payment_date = timezone.now().date()
        p.save()

        updated_records.append(p)
        remaining_amount -= pay_now
    return remaining_amount, updated_records


def apply_one_time_payment(student, payment_type, paid_amount):
    remaining_amount = paid_amount
    updated_records = []

    if payment_type == 'exam':
        dues = student.student_exam_fee_payments.filter(payment_status__in=['due', 'partial'])
    elif payment_type == 'other':
        dues = student.other_fee_students.filter(payment_status__in=['due', 'partial'])
    else:
        return remaining_amount, updated_records

    for p in dues:
        if remaining_amount <= 0:
            break

        due = p.due_amount or 0
        pay_now = min(due, remaining_amount)
        p.amount_paid += pay_now
        p.due_amount = due - pay_now
        p.payment_status = 'paid' if p.due_amount <= 0 else 'partial'
        p.payment_date = timezone.now().date()
        p.save()

        updated_records.append(p)

        remaining_amount -= pay_now
    return remaining_amount, updated_records







from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from accounting.models import Account, JournalEntry, JournalEntryLine, FiscalYear
from core.models import TaxPolicy

Q = Decimal("0.01")

def money(val):   
    return Decimal(val or 0).quantize(Q, ROUND_HALF_UP)

def calculate_tax(amount, tax_policy):
    gross = money(amount)
    vat_rate = money(tax_policy.vat_rate) / 100
    ait_rate = money(tax_policy.ait_rate) / 100

    vat = Decimal("0.00")
    ait = Decimal("0.00")

    # VAT
    if vat_rate > 0:
        if tax_policy.vat_type == "inclusive":
            vat = gross - (gross / (1 + vat_rate))
            base = gross - vat
        else:
            vat = gross * vat_rate
            base = gross
    else:
        base = gross

    # AIT
    if ait_rate > 0:
        if tax_policy.ait_type == "inclusive":
            ait = base - (base / (1 + ait_rate))
        else:
            ait = base * ait_rate

    net_income = base - ait
    cash_received = base + vat  # Cash received does NOT subtract AIT

    return {
        "income": money(net_income),
        "vat": money(vat),
        "ait": money(ait),
        "cash": money(cash_received),
    }



@transaction.atomic
def create_school_fee_journal_entry(    
    *,
    payment_date,
    reference,
    student,
    fees: dict,
    tax_policy,
    created_by=None
):
   
    from students.models import Student
    
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("Active FiscalYear required")

    if not tax_policy:
        raise ValueError("Active TaxPolicy required")
   
    cash_account = Account.objects.get(code="1110")  # Cash on Hand    
    income_accounts = {
        'tuition': Account.objects.get(code="4210"),     # Tuition Fee Income
        'admission': Account.objects.get(code="4220"),   # Admission Fee Income
        'hostel': Account.objects.get(code="4230"),      # Hostel Revenue (Hostel Fee)
        'transport': Account.objects.get(code="4240"),   # Transport Revenue (Transport Fee)
    }

    vat_account = Account.objects.get(code="2131")  # Output VAT Payable
    ait_account = Account.objects.get(code="2132")  # AIT Payable

    # --- Create Journal Entry ---
    entry = JournalEntry.objects.create(
        date=payment_date,
        fiscal_year=fiscal_year,
        reference=reference,
        description=f"Student fee payment - {student.name}",
        created_by=created_by
    )

    total_cash = Decimal("0.00")
    total_credit = Decimal("0.00")

    def post_fee(amount, fee_type, label):
        nonlocal total_cash, total_credit
        amount = money(amount)
        if amount <= 0:
            return

        t = calculate_tax(amount, tax_policy)

        # Income
        JournalEntryLine.objects.create(
            entry=entry,
            account=income_accounts[fee_type],
            credit=t["income"],
            description=f"{label} Income"
        )
        total_credit += t["income"]

        # VAT
        if t["vat"] > 0:
            JournalEntryLine.objects.create(
                entry=entry,
                account=vat_account,
                credit=t["vat"],
                description=f"{label} VAT Payable"
            )
            total_credit += t["vat"]

        # AIT
        if t["ait"] > 0:
            JournalEntryLine.objects.create(
                entry=entry,
                account=ait_account,
                credit=t["ait"],
                description=f"{label} AIT Payable"
            )
            total_credit += t["ait"]

        # Cash received
        total_cash += t["cash"]

    # --- Post each fee ---
    for fee_type, amount in fees.items():
        label = fee_type.capitalize()
        post_fee(amount, fee_type, label)

    # --- Cash / Bank Debit ---
    JournalEntryLine.objects.create(
        entry=entry,
        account=cash_account,
        debit=money(total_cash),
        description="Cash / Bank received from student"
    )

    # --- Safety check ---
    debit = sum(l.debit for l in entry.lines.all())
    credit = sum(l.credit for l in entry.lines.all())
    if money(debit) != money(credit):
        raise AssertionError(
            f"Journal NOT balanced | Debit={debit} Credit={credit}"
        )

    return entry

"""

fees = {
    'tuition': Decimal("4000"),
    'admission': Decimal("2000"),
    'hostel': Decimal("1500")
}

journal_entry = create_school_fee_journal_entry(
    payment_date=date.today(),
    reference="INV-1001",
    student=my_student,
    fees=fees,
    created_by=request.user
)

"""
