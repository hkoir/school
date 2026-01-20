from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from .models import (
    UniversityTermInvoice,StudentSubjectResult,StudentTermResult, StudentSubjectEnrollment
)


def generate_term_invoice(*, enrollment, term_registration):
    student = enrollment.student
    academic_session = enrollment.academic_session
    term = term_registration.term
    fee_structure = enrollment.fee_structure

    enrollments = StudentSubjectEnrollment.objects.filter(
        student=student,
        academic_session=academic_session,
        term_registration=term_registration
    )

    total_subjects = enrollments.count()
    total_credits = Decimal('0.00')
    tuition_fee = Decimal('0.00')

    admission_fee = Decimal('0.00')
    already_paid_admission = UniversityTermInvoice.objects.filter(
        student=student,
        program=enrollment.program,
        admission_fee__gt=0
    ).exists()

    if fee_structure.admission_fee and not already_paid_admission:
        admission_fee = fee_structure.admission_fee.total_admission_fee or Decimal('0.00')


    for enr in enrollments:
        subject = enr.subject_offering.subject
        credit = subject.total_credit or Decimal('0.00')

        rate = (
            subject.per_credit_fee_override
            if subject.per_credit_fee_override
            else fee_structure.per_credit_fee
        )

        total_credits += credit
        tuition_fee += credit * rate   

    total_payable = tuition_fee + admission_fee

    invoice = UniversityTermInvoice.objects.create(
        student=student,
        academic_session=academic_session,
        academic_year = timezone.now().year,
        program=enrollment.program,
        level=term_registration.level,
        term=term,
        total_subjects=total_subjects,
        total_credits=total_credits,
        per_credit_fee=fee_structure.per_credit_fee,
        tuition_fee=tuition_fee,
        admission_fee=admission_fee,
        total_payable=total_payable,
        due_amount=total_payable
    )

    return invoice


def generate_term_invoice_updated(*, enrollment, term_registration):
    student = enrollment.student
    academic_session = enrollment.academic_session
    term = term_registration.term
    fee_structure = enrollment.fee_structure

    # Subject-based fees
    enrollments = StudentSubjectEnrollment.objects.filter(
        student=student,        
        term_registration=term_registration
    )

    total_subjects = enrollments.count()
    total_credits = Decimal('0.00')
    tuition_fee = Decimal('0.00')

    for enr in enrollments:
        subject = enr.subject_offering.subject
        credit = subject.total_credit or Decimal('0.00')
        rate = subject.per_credit_fee_override or fee_structure.per_credit_fee
        total_credits += credit
        tuition_fee += credit * rate

    # Admission Fee logic
    admission_fee = Decimal('0.00')
    policy = fee_structure.admission_fee
    if policy:
        # Filter admission fee items due for this term
        term_items = policy.varsity_admission_fees.filter(due_terms=term)
        admission_fee = sum(item.amount for item in term_items)

    total_payable = tuition_fee + admission_fee

    invoice = UniversityTermInvoice.objects.create(
        student=student,
        enrollment=enrollment,
        academic_session=academic_session,
        academic_year=timezone.now().year,
        program=enrollment.program,
        level=term_registration.level,
        term=term,
        total_subjects=total_subjects,
        total_credits=total_credits,
        per_credit_fee=fee_structure.per_credit_fee,
        tuition_fee=tuition_fee,
        admission_fee=admission_fee,
        total_payable=total_payable,
        due_amount=total_payable
    )

    return invoice


def is_fee_cleared(student, academic_session, term):  
    try:
        invoice = UniversityTermInvoice.objects.get(
            student=student,
            academic_session=academic_session,
            term=term
        )
    except UniversityTermInvoice.DoesNotExist:
        return False 

    total_paid = invoice.total_paid or Decimal('0.00')
    total_amount = invoice.total_payable or Decimal('0.00')

    return total_paid >= total_amount



def calculate_and_update_term_result(student, exam):
    results = StudentSubjectResult.objects.filter(
        student=student,
        exam=exam,
        is_absent=False,
        is_published=True
    )

    if not results.exists():
        return

    total_credits = results.aggregate(
        total=Sum('credit')
    )['total'] or 0

    total_weighted = results.aggregate(
        total=Sum('weighted_points')
    )['total'] or 0

    gpa = round(
        total_weighted / total_credits, 2
    ) if total_credits > 0 else 0

    StudentTermResult.objects.update_or_create(
        student=student,
        academic_session=exam.academic_session,
        program=exam.program,
        level=exam.level,
        term=exam.term,
        is_published =True,
        defaults={
            'academic_year': exam.academic_year,
            'total_credits': total_credits,
            'gpa': gpa,
            'is_published': True
        }
    )

def calculate_term_gpa(student, term, academic_session):  
    results = StudentSubjectResult.objects.filter(
        student=student,
        term=term,
        academic_session=academic_session,
        is_published=True
    )

    total_weighted_points = sum(r.weighted_points for r in results)
    total_credits = sum(r.credit for r in results)

    gpa = round(total_weighted_points / total_credits, 2) if total_credits else 0
    return gpa, total_credits


def calculate_cgpa(student, academic_session=None):  
    qs = StudentSubjectResult.objects.filter(
        student=student,
        is_published=True
    ).order_by('subject_offering__subject', '-created_at')

    if academic_session:
        qs = qs.filter(academic_session=academic_session)

    latest_results = {}
    total_weighted_points = Decimal("0.00")
    total_credits = Decimal("0.00")

    for r in qs:
        subject_id = r.subject_offering.subject_id
        if subject_id in latest_results:
            continue  
        latest_results[subject_id] = r
        total_weighted_points += r.weighted_points
        total_credits += r.credit

    cgpa = round(total_weighted_points / total_credits, 2) if total_credits > 0 else 0

    return cgpa, total_credits




from datetime import date
from decimal import Decimal
from django.db import transaction
from core.models import TaxPolicy
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from accounting.models import (
    JournalEntry,
    JournalEntryLine,
    Account,
    FiscalYear,   
)

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
    cash_received = base + vat  # 💡 Cash does NOT subtract AIT

    return {
        "income": money(net_income),
        "vat": money(vat),
        "ait": money(ait),
        "cash": money(cash_received),
    }


@transaction.atomic
def create_student_fee_journal_entry(
    *,
    payment_date,
    reference,
    student_name,
    tax_policy,
    tuition_amount=Decimal("0.00"),
    admission_amount=Decimal("0.00"),
    created_by=None
):
    fiscal_year = FiscalYear.get_active()
    if not tax_policy:
        raise ValueError("Active TaxPolicy required")

    # Accounts
    cash_account = Account.objects.get(code="1110")
    tuition_account = Account.objects.get(code="4210")
    admission_account = Account.objects.get(code="4220")
    vat_account = Account.objects.get(code="2131")
    ait_account = Account.objects.get(code="2132")

    entry = JournalEntry.objects.create(
        date=payment_date,
        fiscal_year=fiscal_year,
        reference=reference,
        description=f"Student fee payment - {student_name}",
        created_by=created_by
    )

    total_cash = Decimal("0.00")
    total_credit = Decimal("0.00")

    def post_fee(amount, income_account, label):
        nonlocal total_cash, total_credit

        amount = money(amount)
        if amount <= 0:
            return

        t = calculate_tax(amount, tax_policy)

        # Income
        JournalEntryLine.objects.create(
            entry=entry,
            account=income_account,
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

    # Post fees
    post_fee(tuition_amount, tuition_account, "Tuition Fee")
    post_fee(admission_amount, admission_account, "Admission Fee")

    # Cash / Bank
    JournalEntryLine.objects.create(
        entry=entry,
        account=cash_account,
        debit=money(total_cash),
        description="Student Fee Received"
    )

    # Safety check
    debit = sum(l.debit for l in entry.lines.all())
    credit = sum(l.credit for l in entry.lines.all())
    if money(debit) != money(credit):
        raise AssertionError(
            f"Journal NOT balanced | Debit={debit} Credit={credit}"
        )

    return entry


"""
@login_required
def receive_student_fee(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.is_posted:
        messages.warning(request, "Journal entry already created.")
        return redirect("payment_detail", payment_id)

    entry = create_student_fee_journal_entry(
        payment_date=payment.paid_date or date.today(),
        reference=f"PAY-{payment.id}",
        student_name=payment.student.name,
        tuition_amount=Decimal(payment.tuition_fee_paid or 0),
        admission_amount=Decimal(payment.admission_fee_payment or 0),       
        created_by=request.user
    )

    payment.journal_entry = entry
    payment.is_posted = True
    payment.save()

    messages.success(request, "Payment posted to accounts successfully.")
    return redirect("payment_detail", payment_id)


"""
