

from django.db.models import Sum, Q
from datetime import date
from payments.models import AdmissionFeePayment,Payment

from datetime import date
from django.utils.timezone import now
from django.db import transaction
from core.models import Employee
from finance.models import SalaryPayment, Expense 



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




def calculate_revenue(start_date, end_date):  
    tuition_revenue = Payment.objects.filter(
        payment_date__range=(start_date, end_date),
        monthly_tuition_fee_paid__gt=0
    ).aggregate(total=Sum('monthly_tuition_fee_paid'))['total'] or 0


    admission_revenue_1 = Payment.objects.filter(
        payment_date__range=(start_date, end_date),
        admission_fee_paid__gt=0
    ).aggregate(total=Sum('admission_fee_paid'))['total'] or 0

    admission_revenue_2 = AdmissionFeePayment.objects.filter(
        payment__payment_date__range=(start_date, end_date),
        amount_paid__gt=0
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    admission_revenue = max(admission_revenue_1, admission_revenue_2)

    total_revenue = tuition_revenue + admission_revenue
    return {
        'tuition_revenue': tuition_revenue,
        'admission_revenue': admission_revenue,
        'total_revenue': total_revenue,
    }
