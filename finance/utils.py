
from django.db.models import Sum, Q
from datetime import date
from payments.models import AdmissionFeePayment,Payment

from datetime import date
from django.utils.timezone import now
from django.db import transaction
from core.models import Employee
from finance.models import SalaryPayment, Expense 
from payments.models import PaymentInvoice



def auto_generate_salary_expenses_for_month(target_month: date):
    active_employees = Employee.objects.filter(active=True)
    total_eligible = active_employees.count()
    count_created = 0

    for employee in active_employees:
        if SalaryPayment.objects.filter(employee=employee, month=target_month).exists():
            continue

        net_salary = employee.salary_structure.net_salary()
        if net_salary == 0:
            continue

        with transaction.atomic():
            SalaryPayment.objects.create(
                employee=employee,
                month=target_month,
                amount=net_salary,
                is_posted_to_expense=True
            )
            Expense.objects.create(
                category='SALARY',
                amount=net_salary,
                date=now().date(),
                description=f"Auto Salary for {employee.name} ({target_month.strftime('%B %Y')})",
                employee=employee
            )

            count_created += 1

    return count_created, total_eligible


from payments.models import (
    TuitionFeePayment,
    AdmissionFeePayment,
    HostelRoomPayment,
    TransportPayment,
    ExamFeePayment,
    OtherFeePayment
)
from university_management.models import UniversityTermInvoice, UniversityPayment

def calculate_revenue(start_date, end_date):     

    tuition_revenue = TuitionFeePayment.objects.filter(
        payment_date__range=(start_date, end_date),
        amount_paid__gt=0
    ).aggregate(total=Sum('amount_paid'))['total'] or 0   

    admission_revenue = AdmissionFeePayment.objects.filter(
        payment_date__range=(start_date, end_date),
        amount_paid__gt=0
    ).aggregate(total=Sum('amount_paid'))['total'] or 0   

    transport_revenue = PaymentInvoice.objects.filter(
        created_at__range=(start_date, end_date),
        invoice_type ='transport'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    hostel_revenue = PaymentInvoice.objects.filter(
        created_at__range=(start_date, end_date),
        invoice_type ='hostel'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    exam_fee_revenue = PaymentInvoice.objects.filter(
        created_at__range=(start_date, end_date),
        invoice_type ='exam'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    other_revenue = PaymentInvoice.objects.filter(
        created_at__range=(start_date, end_date),
        invoice_type ='other'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    varsity_admission = UniversityPayment.objects.filter(
        paid_at__range=(start_date, end_date),
        admission_paid__gt=0
    ).aggregate(total=Sum('admission_paid'))['total'] or 0

    varsity_tuition = UniversityPayment.objects.filter(
        paid_at__range=(start_date, end_date),
        tuition_paid__gt=0
    ).aggregate(total=Sum('tuition_paid'))['total'] or 0

  
    total_revenue = varsity_tuition + varsity_admission + tuition_revenue + admission_revenue + transport_revenue + hostel_revenue + exam_fee_revenue + other_revenue
    return {
        'tuition_revenue': tuition_revenue,
        'admission_revenue': admission_revenue,

        'varsity_tuition_revenue': varsity_tuition,
        'varsity_admission_revenue': varsity_admission,

        'transport_revenue':transport_revenue,
        'hostel_revenue':hostel_revenue,
        'exam_fee_revenue':exam_fee_revenue,
        'other_revenue':other_revenue,
        'total_revenue': total_revenue,
    }


def calculate_revenue_and_outstanding(start_date, end_date):
    result = {}

    categories = [
        ('school_tuition', TuitionFeePayment),
        ('school_admission', AdmissionFeePayment),
        ('hostel', HostelRoomPayment),
        ('transport', TransportPayment),
        ('exam', ExamFeePayment),
        ('other', OtherFeePayment),
    ]

    for key, model in categories:
        qs = model.objects.filter(payment_date__range=(start_date, end_date))
        paid = qs.aggregate(total=Sum('amount_paid'))['total'] or 0
        payable = qs.aggregate(total=Sum('total_amount'))['total'] or 0
        outstanding = payable - paid
        result[key] = {'paid': paid, 'payable': payable, 'outstanding': outstanding}

    # Varsity payments
    varsity_invoice_qs = UniversityTermInvoice.objects.filter(created_at__range=(start_date, end_date))
    varsity_payments_qs = UniversityPayment.objects.filter(paid_at__range=(start_date, end_date))

    # Varsity Tuition
    varsity_tuition_paid = varsity_payments_qs.aggregate(total=Sum('tuition_paid'))['total'] or 0
    varsity_tuition_payable = varsity_invoice_qs.aggregate(total=Sum('tuition_fee'))['total'] or 0
    varsity_tuition_outstanding = varsity_tuition_payable - varsity_tuition_paid
    result['varsity_tuition'] = {
        'paid': varsity_tuition_paid,
        'payable': varsity_tuition_payable,
        'outstanding': varsity_tuition_outstanding
    }

    # Varsity Admission
    varsity_admission_paid = varsity_payments_qs.aggregate(total=Sum('admission_paid'))['total'] or 0
    varsity_admission_payable = varsity_invoice_qs.aggregate(total=Sum('admission_fee'))['total'] or 0
    varsity_admission_outstanding = varsity_admission_payable - varsity_admission_paid
    result['varsity_admission'] = {
        'paid': varsity_admission_paid,
        'payable': varsity_admission_payable,
        'outstanding': varsity_admission_outstanding
    }

    # ---- TOTALS ----
    # Only sum over dictionary items (skip totals themselves)
    result['total_paid'] = sum(v['paid'] for k, v in result.items() if isinstance(v, dict))
    result['total_payable'] = sum(v['payable'] for k, v in result.items() if isinstance(v, dict))
    result['total_outstanding'] = sum(v['outstanding'] for k, v in result.items() if isinstance(v, dict))

    return result


from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from accounting.models import Account, JournalEntry, JournalEntryLine, FiscalYear
from core.models import TaxPolicy

Q = Decimal("0.01")

def money(val):   
    return Decimal(val or 0).quantize(Q, ROUND_HALF_UP)


def calculate_purchase_tax(amount, tax_policy):
    gross = money(amount)
    vat_rate = money(tax_policy.vat_rate) / 100
    ait_rate = money(tax_policy.ait_rate) / 100

    vat = Decimal("0.00")
    ait = Decimal("0.00")

    base = gross

    # VAT (input)
    if vat_rate > 0:
        if tax_policy.vat_type == "inclusive":
            vat = gross - (gross / (1 + vat_rate))
            base = gross - vat
        else:
            vat = gross * vat_rate

    # AIT (withholding)
    if ait_rate > 0:
        if tax_policy.ait_type == "inclusive":
            ait = base - (base / (1 + ait_rate))
        else:
            ait = base * ait_rate

    # Net cash paid to supplier
    cash_paid = (base + vat) - ait

    return {
        "base": money(base),
        "vat": money(vat),
        "ait": money(ait),
        "cash": money(cash_paid),
    }


@transaction.atomic
def create_purchase_journal_entry(
    *,
    purchase_date,
    reference,
    vendor,
    amount,
    account_code,    # Expense or Asset account
    created_by=None,
    description="Purchase",
    tax_policy
):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("Active FiscalYear required")
  
    if not tax_policy:
        raise ValueError("Active TaxPolicy required")

   # Accounts
    cash_account = Account.objects.get(code="1110")       # Cash on Hand / Bank
    input_vat_account = Account.objects.get(code="1180")  # Input VAT Recoverable (Asset)
    ait_payable_account = Account.objects.get(code="2132")  # AIT Payable (Liability)
    expense_or_asset_account = Account.objects.get(code=account_code)  # e.g. 5240/supplies or 1210/asset


    t = calculate_purchase_tax(amount, tax_policy)

    entry = JournalEntry.objects.create(
        date=purchase_date,
        fiscal_year=fiscal_year,
        reference=reference,
        description=f"{description} from {vendor.name}",
        created_by=created_by
    )

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    # 1) Asset/Expense Base
    JournalEntryLine.objects.create(
        entry=entry,
        account=expense_or_asset_account,
        debit=t["base"],
        description=description
    )
    total_debit += t["base"]

    # 2) Input VAT
    if t["vat"] > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=input_vat_account,
            debit=t["vat"],
            description="Input VAT"
        )
        total_debit += t["vat"]

    # 3) AIT Payable (withholding)
    if t["ait"] > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable_account,
            credit=t["ait"],
            description="AIT Payable"
        )
        total_credit += t["ait"]

    # 4) Cash/Bank Payment
    JournalEntryLine.objects.create(
        entry=entry,
        account=cash_account,
        credit=t["cash"],
        description="Payment to Vendor"
    )
    total_credit += t["cash"]

    # --- Safety Check ---
    if money(total_debit) != money(total_credit):
        raise AssertionError(
            f"Journal NOT balanced | Debit={total_debit} Credit={total_credit}"
        )

    return entry
