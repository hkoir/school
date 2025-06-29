
from django.urls import path
from .import views


app_name = 'inventory'



urlpatterns = [

path('create_supplier/', views.create_supplier, name='create_supplier'), 
path('update_supplier/<int:id>/', views.create_supplier, name='update_supplier'),
path('delete_supplier/<int:id>/', views.delete_supplier, name='delete_supplier'),   
path('create_warehouse/', views.manage_warehouse, name='create_warehouse'),
path('update_warehouse/<int:id>/', views.manage_warehouse, name='update_warehouse'),
path('delete_warehouse/<int:id>/', views.delete_warehouse, name='delete_warehouse'),
path('', views.product_dashboard, name='product_dashboard'), 
path('product_list/', views.product_list, name='product_list'),
path('create_product/', views.manage_product, name='create_product'),
path('update_product/<int:id>/', views.manage_product, name='update_product'),
path('delete_product/<int:id>/', views.delete_product, name='delete_product'),
path('product_data/<int:product_id>/', views.product_data, name='product_data'),

path('create_category/', views.manage_category, name='create_category'),
path('update_category/<int:id>/', views.manage_category, name='update_category'),
path('delete_category/<int:id>/', views.delete_category, name='delete_category'),    
path('inventory_transaction_view/', views.inventory_transaction_view, name='inventory_transaction_view'),  
path('inventory_dashboard/', views.inventory_dashboard, name='inventory_dashboard'), 



]   