
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'teachers'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),
    path('create_teacher/', views.manage_teacher, name='create_teacher'),    
    path('update_teacher/<int:id>/', views.manage_teacher, name='update_teacher'),    
    path('delete_teacher/<int:id>/', views.delete_teacher, name='delete_teacher'),  
    path('view_teacher_vcard/', views.view_teacher_vcard, name='view_teacher_vcard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
  
]
