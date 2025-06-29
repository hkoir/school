
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'performance'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),
  
]