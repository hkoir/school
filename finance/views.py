

from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import F
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib import messages
import json
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from.models import Asset
from.forms import AssetForm

from payments.models import PaymentInvoice
from django.db import models
from finance.models import Expense
from university_management.models import UniversityPayment


from .forms import PurchaseOrderForm, PurchaseItemFormSet,PurchaseOrderApprovalForm,PurchasePaymentForm
from inventory.models import Inventory,InventoryTransaction,Product,Category
from inventory.forms import InventoryTransactionForm
from.utils import create_purchase_journal_entry
from.models import Asset,Expense,PurchaseOrder
from decimal import Decimal


@login_required
def manage_purchase_order(request, pk=None):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk) if pk else None

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, instance=purchase_order)
        formset = PurchaseItemFormSet(request.POST, instance=purchase_order)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():               
                purchase_order = form.save(commit=False)
                if not purchase_order.approval_status:
                    purchase_order.approval_status = "pending"
                purchase_order.save()            
                items = formset.save(commit=False)              
                for obj in formset.deleted_objects:
                    obj.delete()               
                for item in items:
                    item.purchase = purchase_order
                    item.save()               
                purchase_order.save()  

            messages.success(request, "Purchase Order saved successfully!")
            return redirect("finance:purchase_order_detail", pk=purchase_order.pk)

        else:
            print(form.errors, formset.errors)

    else:
        form = PurchaseOrderForm(instance=purchase_order)
        formset = PurchaseItemFormSet(instance=purchase_order)

    return render(request, "finance/purchase/purchase_order_form.html", {
        "form": form,
        "formset": formset,
        "order": purchase_order,
    })


@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all().order_by('-id') 
    vendor_id = request.GET.get('vendor')
    status = request.GET.get('status')
    if vendor_id:
        orders = orders.filter(vendor_id=vendor_id)
    if status:
        orders = orders.filter(approval_status=status)

    return render(request, "finance/purchase/purchase_order_list.html", {
        "orders": orders
    })

@login_required
def purchase_order_detail(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, "finance/purchase/purchase_order_detail.html", {
        "order": purchase_order,
    })


@login_required
def purchase_order_approve(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == "POST":
        form = PurchaseOrderApprovalForm(request.POST, instance=purchase_order)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.date_approved = timezone.now()
            form_instance.save()
            messages.success(request, "Purchase Order approval updated!")
            return redirect("finance:purchase_order_detail", pk=pk)
    else:
        form = PurchaseOrderApprovalForm(instance=purchase_order)

    return render(request, "finance/purchase/purchase_order_approval_form.html", {
        "form": form,
        "order": purchase_order,
    })


@login_required
def purchase_order_payment(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == "POST":
        form = PurchasePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.purchase = purchase_order
            payment.payment_date = timezone.now()
            payment.save()   

            if payment.purchase_type in ['inventory','expense']:
                account_code = '5240'
            else:
                account_code = '1210'                   

            create_purchase_journal_entry(
                purchase_date=payment.payment_date,
                reference=f'purchase order-{purchase_order}',
                vendor=purchase_order.vendor,                
                amount = payment.purchase.subtotal, 
                tax_policy = payment.purchase.vat_ait_policy,
                account_code=account_code )

            messages.success(request, "Payment recorded successfully!")
            return redirect("finance:purchase_order_detail", pk=pk)
    else:
        form = PurchasePaymentForm()

    return render(request, "finance/purchase/purchase_order_payment_form.html", {
        "form": form,
        "purchase_order": purchase_order,
    })



@login_required
def update_inventory(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    need_inventory_inputs = any(
        item.purchase_type == 'inventory' for item in purchase_order.purchase_items.all()
    )

    if request.method == "POST":
        form = InventoryWarehouseForm(request.POST)
        if need_inventory_inputs and not form.is_valid():
            return render(request, "finance/purchase/update_inventory.html", {
                "form": form,
                "order": purchase_order,
                "need_inventory_inputs": need_inventory_inputs,
            })
        if form.is_valid():
            warehouse = form.cleaned_data['warehouse']
            location = form.cleaned_data['location']
            inventory_transaction=None

            with transaction.atomic():             
                InventoryTransaction.objects.filter(
                    purchase_order=purchase_order,
                    transaction_type="INBOUND"
                ).delete()
                
                for item in purchase_order.purchase_items.all():
                    if not item.product or not item.quantity:
                        continue

                    if item.purchase_type == 'inventory':
                        inventory, _ = Inventory.objects.get_or_create(
                            warehouse=warehouse,
                            location=location,
                            product=item.product,
                            defaults={'quantity': 0}
                        )

                        inventory.quantity += item.quantity
                        inventory.save()

                        inventory_transaction = InventoryTransaction.objects.create(
                            user=request.user,
                            product=item.product,
                            warehouse=warehouse,
                            location=location,
                            quantity=item.quantity,
                            transaction_type="INBOUND",
                            purchase_order=purchase_order,
                            transaction_date=timezone.now(),
                            remarks=f"Purchase Order #{pk} inbound {item.quantity}",
                        )

                    elif item.purchase_type == 'expense':
                        Expense.objects.create(
                            category='OTHER',
                            amount=item.unit_price * item.quantity,
                            description=f'Purchase consumable item: {item.product}',
                            inventory_purchase=inventory_transaction,
                            date=timezone.now()
                        )

                    elif item.purchase_type == 'asset':
                        asset = Asset.objects.create(
                            name=str(item.product),
                            value=item.unit_price * item.quantity,
                            depreciation_rate=Decimal('5.0'),
                            purchase_date=purchase_order.date_approved or timezone.now()
                        )    
                        asset.apply_asset_depreciation()               

                purchase_order.approval_status = "closed"
                purchase_order.save()

            messages.success(request, "Inventory updated successfully!")
            return redirect("finance:purchase_order_detail", pk=pk)
    else:
        form = InventoryWarehouseForm()

    return render(request, "finance/purchase/update_inventory.html", {
        "form": form,
        "order": purchase_order,
        "need_inventory_inputs": need_inventory_inputs,
    })



@login_required
def accounts_finance_dashboard(request):
    from django.utils import timezone
    from datetime import date

    current_year = timezone.now().year
    current_month = timezone.now().month

    total_fees_collected = PaymentInvoice.objects.filter(        
        created_at__year=current_year
    ).aggregate(total=models.Sum('paid_amount'))['total'] or 0

    monthly_fees_collected = PaymentInvoice.objects.filter(      
        created_at__year=current_year,
        created_at__month=current_month
    ).aggregate(total=models.Sum('paid_amount'))['total'] or 0

    outstanding_fees = PaymentInvoice.objects.filter(
        payment_status="due"
    ).aggregate(total=models.Sum('due_amount'))['total'] or 0

    total_expenses = Expense.objects.filter(
        date__year=current_year
    ).aggregate(total=models.Sum('amount'))['total'] or 0
   

    recent_collections = PaymentInvoice.objects.filter(        
    ).select_related('student').order_by('-created_at')[:10]

    varsity_recent_collections = UniversityPayment.objects.filter(        
    ).select_related('student').order_by('-paid_at')[:10]

    recent_expenses = Expense.objects.all().order_by('-date')[:10]

    varsity_tuition = UniversityPayment.objects.filter(        
        paid_at__year=current_year,
        paid_at__month=current_month
    ).aggregate(total=models.Sum('tuition_paid'))['total'] or 0

    varsity_admission = UniversityPayment.objects.filter(       
        paid_at__year=current_year,
        paid_at__month=current_month
    ).aggregate(total=models.Sum('admission_paid'))['total'] or 0

    varsity_collection = UniversityPayment.objects.filter(
        paid_at__year=current_year
    ).aggregate(
        tuition=models.Sum('tuition_paid'),
        admission=models.Sum('admission_paid')
    )

    total_varsity_fees_collected = (varsity_collection['tuition'] or 0) + (varsity_collection['admission'] or 0)

    net_profit = (total_fees_collected + total_varsity_fees_collected) - total_expenses

    Varsity_school_this_month = varsity_tuition + varsity_admission + monthly_fees_collected
    Varsity_school_this_year = total_fees_collected +  total_varsity_fees_collected

    context = {
        "current_year": current_year,
        "monthly_fees_collected": monthly_fees_collected,
        "total_fees_collected": total_fees_collected,
        "outstanding_fees": outstanding_fees,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "recent_collections": recent_collections,
        "recent_expenses": recent_expenses,

        "varsity_tuition": varsity_tuition,
        "varsity_admission": varsity_admission,       
        'total_varsity_fees_collected': total_varsity_fees_collected,
        'Varsity_school_this_month':Varsity_school_this_month,
        'Varsity_school_this_year':Varsity_school_this_year,
        'varsity_recent_collections':varsity_recent_collections
    }
    
    return render(request, "finance/finance_dashboard.html", context)


@login_required
def manage_asset(request, id=None):  
    instance = get_object_or_404(Asset, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =AssetForm(request.POST or None, request.FILES or None, instance=instance)
            
    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('finance:create_asset') 

    datas = Asset.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/manage_asset.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_asset(request, id):
    instance = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('finance:create_asset')

    messages.warning(request, "Invalid delete request!")
    return redirect('finance:create_asset')





#================================ Profit loss ==============================


from django.utils.timezone import now
from datetime import datetime
from finance.models import Expense
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from finance.utils import calculate_revenue
from finance.utils import auto_generate_salary_expenses_for_month
from .forms import ExpenseForm




# @user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Finance').exists())
@login_required
def generate_monthly_salaries(request):
    if request.method == "POST":
        month_str = request.POST.get("month")
        try:
            target_month = datetime.strptime(month_str, "%Y-%m").date().replace(day=1)
        except ValueError:
            messages.error(request, "Invalid month format.")
            return redirect(request.path)

        created, total = auto_generate_salary_expenses_for_month(target_month)
        if created == 0:
            messages.info(request, f"Salary payments for {target_month.strftime('%B %Y')} were already generated.")
            return redirect(request.path)
        elif created < total:
            messages.warning(request, f"{created} new salaries generated. {total - created} already existed for {target_month.strftime('%B %Y')}.")
            return redirect(request.path)
        else:
            messages.success(request, f"All {created} salaries successfully generated for {target_month.strftime('%B %Y')}.")
            return redirect(request.path)

    return render(request, "finance/generate_salaries.html")




@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            if not expense.date:
                expense.date = timezone.now().date()
            expense.save()
            return redirect('finance:expense_list')  # adjust to your app's name
    else:
        form = ExpenseForm()
    return render(request, 'finance/add_expense.html', {'form': form})




def asset_list(request):
    assets = Asset.objects.all().order_by('-purchase_date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:        
        start_date = end_date = None

    if start_date and end_date:
        assets =  assets.filter(purchase_date__range=[start_date, end_date])
   
    paginator = Paginator(assets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'finance/asset_list.html', {
        'assets': assets,
        'page_obj':page_obj
    })



def expense_list(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    expenses = Expense.objects.all().order_by('-date')
    start_date = end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        start_date = end_date = None

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])


    top_expenses = expenses.values('category').annotate(total_amount=Sum('amount')).order_by('-total_amount')[:10]
    labels = [e['category'] for e in top_expenses]
    data = [float(e['total_amount']) for e in top_expenses]
    colors = ['#0d6efd', '#198754', '#dc3545', '#fd7e14', '#6f42c1', '#20c997', '#0dcaf0', '#ffc107', '#6610f2', '#d63384'][:len(top_expenses)]

    chart_data_json = json.dumps({
        'bar': {
            'labels': labels,
            'data': data,
            'colors': colors
        },
        'pie': {
            'labels': labels,
            'data': data,
            'colors': colors
        }
    })


    
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/expense_list.html', {
        'expenses': expenses,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'page_obj':page_obj,
        'chart_data_json': chart_data_json
    })

from payments.models import PaymentInvoice

def revenue_list(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    revenue= Payment.objects.all().order_by('-payment_date')
    other_revenue= PaymentInvoice.objects.all().order_by('-created_at')

    start_date = end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:   
        start_date = end_date = None

    if start_date and end_date:
        revenue = revenue.filter(payment_date__range=[start_date, end_date])
        other_revenue = other_revenue.filter(created_at__range=[start_date, end_date], invoice_type__in =['transport','hostel','exam','other'])
     
    paginator = Paginator(revenue, 10)
    page_number1 = request.GET.get('page1')
    page_obj1 = paginator.get_page(page_number1)

    paginator = Paginator(other_revenue, 10)
    page_number2 = request.GET.get('page2')
    page_obj2 = paginator.get_page(page_number2)

    return render(request, 'finance/revenue_list.html', {
        'revenue':revenue,
        'other_revenue':other_revenue,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'page_obj1':page_obj1,
        'page_obj2':page_obj2
    })




from datetime import datetime, date, timedelta
from .models import Asset,AssetDepreciationRecord,Shareholders,ShareholderInvestment


def profit_loss_report(request):
    today = now().date()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today_param = request.GET.get('today')
    month_param = request.GET.get('this_month')

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    if today_param:
        start_date = end_date = today
    elif month_param:
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day))

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    revenue = calculate_revenue(start_datetime,end_datetime) 

    other_revenue = revenue['hostel_revenue'] + revenue['transport_revenue'] + revenue['exam_fee_revenue'] + revenue['other_revenue']

    total_expenses = Expense.objects.filter(
        date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))['total'] or 0

    depreciation_total = Expense.objects.filter(
        date__range=(start_date, end_date),
        category="DEPRECIATION"
    ).aggregate(total=Sum('amount'))['total'] or 0

    depreciation_records = AssetDepreciationRecord.objects.filter(
        created_at__range=(start_datetime, end_datetime)
    ).select_related('asset')

    depreciation_expenses = AssetDepreciationRecord.objects.filter(
        created_at__range=(start_datetime, end_datetime)
    ).aggregate(total=Sum('depreciation_amount'))['total'] or 0

    total_asset_value = Asset.objects.aggregate(total=Sum('current_value'))['total'] or 0

    profit_loss = revenue['total_revenue'] - total_expenses - depreciation_expenses
    total_expense_amount = total_expenses + depreciation_expenses

    shareholders = Shareholders.objects.all()
    shareholder_data = [
        {
            'name': sh.name,
            'percentage': sh.ownership_percentage,
            'share_amount': profit_loss * (sh.ownership_percentage / 100)
        }
        for sh in shareholders
    ]

    # ---- Chart Data ----
    chart_data = {
        "bar": {
            "labels": [
                "Tuition", "Admission","Varsity Tuition", " varsity Admission", "Transport",
                "Hostel", "Exam Fee", "Other", "Total Revenue", "Total Expenses"
            ],
            "data": [
                float(revenue['tuition_revenue']),
                float(revenue['admission_revenue']),
                float(revenue['varsity_tuition_revenue']),
                float(revenue['varsity_admission_revenue']),
                float(revenue['transport_revenue']),
                float(revenue['hostel_revenue']),
                float(revenue['exam_fee_revenue']),
                float(revenue['other_revenue']),
                float(revenue['total_revenue']),
                float(total_expenses)
            ],
            "colors": [
                "#007bff", "#28a745","#20c997", "#dc3545" "#ffc107",
                "#17a2b8", "#6f42c1", "#fd7e14", "#68ef08", "#034e25"
            ]
        },
        "pie": {
            "labels": ["Total Revenue", "Total Expenses"],
            "data": [float(revenue['total_revenue']), float(total_expenses)],
            "colors": ["#28a745", "#dc3545"]
        }
    }

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue': revenue,
        'tuition_revenue': revenue['tuition_revenue'],
        'admission_revenue': revenue['admission_revenue'],

        'varsity_tuition_revenue': revenue['varsity_tuition_revenue'],
        'varsity_admission_revenue': revenue['varsity_admission_revenue'],

        'other_revenue':other_revenue,
        'total_revenue': revenue['total_revenue'],
        'total_expenses': total_expenses,
        'total_expense_amount': total_expense_amount,
        'depreciation_total': depreciation_total,
        'depreciation_records': depreciation_records,
        'total_asset_value': total_asset_value,
        'profit_loss': profit_loss,
        'shareholders': shareholder_data,
        'chart_data_json': json.dumps(chart_data),
    }

    return render(request, 'finance/profit_loss_report.html', context)


from .utils import calculate_revenue_and_outstanding  
def finance_dashboard(request):
    today = now().date()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today_param = request.GET.get('today')
    month_param = request.GET.get('this_month')

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    if today_param:
        start_date = end_date = today
    elif month_param:
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day))

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    finance_data = calculate_revenue_and_outstanding(start_datetime, end_datetime)
    varsity_total_paid = finance_data['varsity_tuition']['paid'] + finance_data['varsity_admission']['paid']
    varsity_total_outstanding = finance_data['varsity_tuition']['outstanding'] + finance_data['varsity_admission']['outstanding']
    varsity_total_payable = finance_data['varsity_tuition']['payable'] + finance_data['varsity_admission']['payable']

    # Prepare chart data
    chart_data = {
        "labels": [],
        "paid": [],
        "outstanding": [],
        "colors": []
    }

    category_colors = {
        'school_tuition': '#007bff',
        'school_admission': '#28a745',
        'hostel': '#ffc107',
        'transport': '#20c997',
        'exam': '#6f42c1',
        'other': '#fd7e14',
        'varsity_tuition': '#0d6efd',
        'varsity_admission': "#12e33f",
    }

    for key, data in finance_data.items():
        if key in ['total_paid', 'total_payable', 'total_outstanding']:
            continue
        chart_data['labels'].append(key.replace('_', ' ').title())
        chart_data['paid'].append(float(data['paid']))
        chart_data['outstanding'].append(float(data['outstanding']))
        chart_data['colors'].append(category_colors.get(key, '#6c757d'))

    exclude_keys = ['total_paid', 'total_payable', 'total_outstanding']
    first_row_keys = ['school_tuition', 'school_admission', 'varsity_tuition', 'varsity_admission']
    second_row_keys = ['hostel', 'transport', 'exam', 'other']

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'finance_data': finance_data,
        'chart_data_json': json.dumps(chart_data),
        'today': today_param,
        'this_month': month_param,
        'exclude_keys': exclude_keys,
        'varsity_total_paid': varsity_total_paid,
        'varsity_total_outstanding': varsity_total_outstanding,
        'varsity_total_payable': varsity_total_payable,
        'first_row_keys': first_row_keys,
        'second_row_keys': second_row_keys,
    }

    return render(request, 'finance/dashboard.html', context)


from datetime import date, datetime
from django.db.models import Sum
from payments.models import Payment, AdmissionFeePayment
from finance.models import Expense
import json
from django.db.models import Sum, Min


def management_dashboard(request):
    today = now().date()

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today_param = request.GET.get('today')
    month_param = request.GET.get('this_month')

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    if today_param:
        start_date = end_date = today
    elif month_param:
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day))

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # --- Revenue & Expenses ---
    revenue = calculate_revenue(start_datetime, end_datetime)
    total_revenue = revenue['total_revenue']
    tuition_revenue = revenue['tuition_revenue']
    admission_revenue = revenue['admission_revenue']

    varsity_tuition_revenue = revenue['varsity_tuition_revenue']
    varsity_admission_revenue = revenue['varsity_admission_revenue']

    total_expense = Expense.objects.filter(date__range=(start_datetime, end_datetime)).aggregate(
        total=Sum('amount')
    )['total'] or 0

    net_profit = total_revenue - total_expense

    chart_data = {
        'bar': {
            'labels': ['Revenue', 'Expense'],
            'data': [float(total_revenue), float(total_expense)],
        },
        'pie': {
            'labels': ['Revenue', 'Expense'],
            'data': [float(total_revenue), float(total_expense)],
        }
    }

    context = {
        'tuition_revenue': tuition_revenue,
        'admission_revenue': admission_revenue,
        'varsity_tuition_revenue': varsity_tuition_revenue,
        'varsity_admission_revenue': varsity_admission_revenue,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_profit': net_profit,       
        'start': start_datetime,
        'end': end_datetime,
        'report_start': start_date.strftime('%Y-%m-%d'),
        'report_end': end_date.strftime('%Y-%m-%d'),
        'chart_data_json': json.dumps(chart_data),
    }

    return render(request, 'finance/management_dashboard.html', context)


@login_required
def revenue_details(request):
    filter_type = request.GET.get('filter')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    payments = Payment.objects.all()

    if filter_type == 'today':
        today = date.today()
        payments = payments.filter(payment_date=today)
    elif filter_type == 'month':
        today = date.today()
        payments = payments.filter(payment_date__year=today.year, date__month=today.month)
    elif start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            payments = payments.filter(payment_date__range=(start, end))
        except:
            payments = Payment.objects.none()

    total_revenue = payments.aggregate(total=Sum('total_paid'))['total'] or 0

    context = {
        'payments': payments,
        'total_revenue': total_revenue,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, "finance/revenue_details.html", context)




@login_required
def expenses_details(request):
    filter_type = request.GET.get('filter')  # ❌ remove default "today"
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    expenses = Expense.objects.all()

    # ✅ Prioritize manual date range first
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            expenses = expenses.filter(date__range=(start, end))
            filter_type = 'custom'
        except ValueError:
            expenses = Expense.objects.none()

    elif filter_type == 'this_month':
        today = date.today()
        expenses = expenses.filter(date__year=today.year, date__month=today.month)

    elif filter_type == 'today':
        today = date.today()
        expenses = expenses.filter(date=today)

    # ✅ If no filter or range, show all
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'filter_type': filter_type,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, "finance/expenses_details.html", context)
