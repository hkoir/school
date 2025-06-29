
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
from.forms import AddProductForm,AddCategoryForm,CommonFilterForm
from.forms import ProductSearchForm,InventoryTransactionForm,AddSupplierForm,AddWarehouseForm

from django.utils import timezone
from django.db import transaction

from.models import Product,Supplier,Warehouse




@login_required
def manage_warehouse(request, id=None):  
    instance = get_object_or_404(Warehouse, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"
    form = AddWarehouseForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance=form.save(commit=False)
        form_instance.user=request.user
        form_instance.save()
        messages.success(request, message_text)
        return redirect('inventory:create_warehouse')

    datas = Warehouse.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_warehouse.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })

@login_required
def delete_warehouse(request, id):
    instance = get_object_or_404(Warehouse, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_warehouse')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_warehouse')




@login_required
def supplier_dashboard(request):
    return render(request,'inventory/supplier_dashboard.html')



@login_required
def create_supplier(request, id=None):  
    instance = get_object_or_404(Supplier, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddSupplierForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('inventory:create_supplier')  

    datas = Supplier.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/create_supplier.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_supplier(request, id):
    instance = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_supplier')  

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_supplier') 







@login_required
def product_dashboard(request):
    return render(request,'inventory/product_dashboard.html')



@login_required
def product_list(request):
    product = None
    products = Product.objects.all().order_by('-supplier')
    form = CommonFilterForm(request.GET or None)  
    if form.is_valid():
        product = form.cleaned_data.get('product_name')
        if product:
            products = products.filter(name__icontains=product.name)  
    
    paginator = Paginator(products, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form=CommonFilterForm()

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'page_obj': page_obj,
        'product': product,
        'form': form,
    })



@login_required
def manage_category(request, id=None):  
    instance = get_object_or_404(Category, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddCategoryForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('inventory:create_category')

    datas = Category.objects.all().order_by('name')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_category.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_category(request, id):
    instance = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_category')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_category')




@login_required
def manage_product(request, id=None):  
    instance = get_object_or_404(Product, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddProductForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('inventory:create_product') 

    datas = Product.objects.all().order_by('supplier')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_product.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_product(request, id):
    instance = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_product')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_product')




@login_required
def product_data(request,product_id):
    product_instance = get_object_or_404(Product,id=product_id)
    return render(request,'inventory/product_data.html',{'product_instance':product_instance})




@login_required
def inventory_transaction_view(request):
    if request.method == 'POST':
        form = InventoryTransactionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,'successfully added product into stock')
            return redirect('inventory:inventory_transaction_view')  
             
    else:
        form = InventoryTransactionForm(user=request.user)

    return render(request, 'inventory/inventory_transaction.html', {'form': form})



@login_required
def inventory_dashboard(request):
    table_data = Inventory.objects.select_related('product', 'warehouse', 'location')
    product=None
    warehouse=None
    location=None
   
    form = ProductSearchForm(request.GET or None)
    if request.method == 'GET':
        form = ProductSearchForm(request.GET or None)
        if form.is_valid():
            product=form.cleaned_data['product']           
            warehouse=form.cleaned_data['warehouse']
            location=form.cleaned_data['location']

            if product:
                table_data = table_data.filter(product__name__icontains=product)
           
            if warehouse:
                table_data = table_data.filter(warehouse__name__icontains=warehouse)
            if location:
                table_data = table_data.filter(location__name__icontains=location)

        else:
            print(form.errors)
          
    
    form = ProductSearchForm()
    datas = table_data 
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('inventory/partials/inventory_table.html', {'page_obj': page_obj})
        return JsonResponse({'html': html})


    inventory_data = table_data.values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        reorder_level=Sum('reorder_level')
    ).order_by('total_quantity')[:10]


    labels = [item['product__name'] for item in inventory_data]
    quantities = [item['total_quantity'] for item in inventory_data]
    reorder_levels = [item['reorder_level'] for item in inventory_data]

  

    context = {
        'labels': json.dumps(labels),
        'quantities': json.dumps(quantities),
        'reorder_levels': json.dumps(reorder_levels),
        'page_obj': page_obj,
        'form':form,
        'product':product,
        'warehouse':warehouse,
        'location':location,
       
    }
  
    
    return render(request, 'inventory/inventory_dashboard.html', context)

