
from django.urls import path
from .import views


app_name = 'finance'



urlpatterns = [

path('create_asset/', views.manage_asset, name='create_asset'),
path('update_asset/<int:id>/', views.manage_asset, name='update_asset'),
path('delete_asset/<int:id>/', views.delete_asset, name='delete_asset'),   

path('generate-monthly-salaries/', views.generate_monthly_salaries, name='generate_monthly_salaries'), 
path('profit-loss-report/', views.profit_loss_report, name='profit_loss_report'),
path('expense_list/', views.expense_list, name='expense_list'),
path('expenses/add/', views.add_expense, name='add_expense'),  
path('asset-list/', views.asset_list, name='asset_list'),

]   
