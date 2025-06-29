from django.shortcuts import render

from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import F
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib import messages
import json
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Inventory
from inventory.models import Product,Category
from django.utils import timezone
from django.db import transaction
from.models import Asset,AssetDepreciationRecord
from.forms import AssetForm
from .forms import ExpenseForm



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





from .models import Asset,AssetDepreciationRecord,Shareholders,ShareholderInvestment

def profit_loss_report(request): 
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = now().date()
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    revenue = calculate_revenue(start_date, end_date)

    total_expenses = Expense.objects.filter(
        date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))['total'] or 0

    depreciation_total = Expense.objects.filter(
        date__range=(start_date, end_date),
        category="DEPRECIATION"
    ).aggregate(total=Sum('amount'))['total'] or 0

    depreciation_records = AssetDepreciationRecord.objects.filter(
        created_at__range=(start_date, end_date)
    ).select_related('asset')

    # ✅ Total current asset value
    total_asset_value = Asset.objects.aggregate(total=Sum('current_value'))['total'] or 0

    profit_loss = revenue['total_revenue'] - total_expenses
    
    shareholders = Shareholders.objects.all()
    shareholder_data = []
    for sh in shareholders:
        share_amount = profit_loss * (sh.ownership_percentage / 100)
        shareholder_data.append({
            'name': sh.name,
            'percentage': sh.ownership_percentage,
            'share_amount': share_amount,
        })

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'tuition_revenue': revenue['tuition_revenue'],
        'admission_revenue': revenue['admission_revenue'],
        'total_revenue': revenue['total_revenue'],
        'total_expenses': total_expenses,
        'depreciation_total': depreciation_total,
        'depreciation_records': depreciation_records,
        'total_asset_value': total_asset_value,  # 👈 add this
        'profit_loss': profit_loss,
        'shareholders': shareholder_data
    }

    return render(request, 'finance/profit_loss_report.html', context)



from django.db.models import Q
from datetime import datetime



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
    return render(request, 'finance/asset_list.html', {
        'assets': assets
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
        # Optional: handle gracefully or fallback
        start_date = end_date = None

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    print('.................................',start_date_str)

    return render(request, 'finance/expense_list.html', {
        'expenses': expenses,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })
