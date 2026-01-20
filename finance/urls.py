


from django.urls import path
from .import views


app_name = 'finance'



urlpatterns = [

path('create_asset/', views.manage_asset, name='create_asset'),
path('update_asset/<int:id>/', views.manage_asset, name='update_asset'),
path('delete_asset/<int:id>/', views.delete_asset, name='delete_asset'),   

path('generate-monthly-salaries/', views.generate_monthly_salaries, name='generate_monthly_salaries'), 
path('profit-loss-report/', views.profit_loss_report, name='profit_loss_report'),

path('expenses/add/', views.add_expense, name='add_expense'),
path('asset-list/', views.asset_list, name='asset_list'),

path('management_dashboard/', views.management_dashboard, name='management_dashboard'),
path('revenue_details/', views.revenue_details, name='revenue_details'),
path('expenses_details/', views.expenses_details, name='expenses_details'),
path('expense_list/', views.expense_list, name='expense_list'), 
path('revenue_list/', views.revenue_list, name='revenue_list'), 

path('accounts_finance_dashboard/', views.accounts_finance_dashboard, name='accounts_finance_dashboard'), 
path('finance_dashboard/', views.finance_dashboard, name='finance_dashboard'), 

path('manage_purchase_order/', views.manage_purchase_order, name='manage_purchase_order'), 
path('purchase_order_list/', views.purchase_order_list, name='purchase_order_list'), 
path('purchase_order_detail/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'), 
path('purchase_order_approve/<int:pk>/', views.purchase_order_approve, name='purchase_order_approve'), 
path('purchase_order_payment/<int:pk>/', views.purchase_order_payment, name='purchase_order_payment'), 
path('update_inventory/<int:pk>/', views.update_inventory, name='update_inventory'), 



]  
