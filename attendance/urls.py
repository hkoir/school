
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'attendance'


urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),

    path('create_weekday/', views.manage_weekday, name='create_weekday'),    
    path('update_weekday/<int:id>/', views.manage_weekday, name='update_weekday'),    
    path('delete_weekday/<int:id>/', views.delete_weekday, name='delete_weekday'),  
    
    path('create_attendance_policy/', views.manage_attendance_policy, name='create_attendance_policy'),    
    path('update_attendance_policy/<int:id>/', views.manage_attendance_policy, name='update_attendance_policy'),    
    path('delete_attendance_policy/<int:id>/', views.delete_attendance_policy, name='delete_attendance_policy'),  
 
    path('create_attendance/', views.manage_attendance, name='create_attendance'),    
    path('update_attendance/<int:id>/', views.manage_attendance, name='update_attendance'),    
    path('delete_attendance/<int:id>/', views.delete_attendance, name='delete_attendance'),  
 
    path('create_attendance_log/', views.manage_attendance_log, name='create_attendance_log'),    
    path('update_attendance_log/<int:id>/', views.manage_attendance_log, name='update_attendance_log'),    
    path('delete_attendance_log/<int:id>/', views.delete_attendance_log, name='delete_attendance_log'),  

    path('attendance_report/', views.attendance_report, name='attendance_report'),  
    path('daily_attendance_summary/', views.daily_attendance_summary, name='daily_attendance_summary'),  


    path('api/attendance/', views.ReceiveAttendanceDataAPIView.as_view(), name='receive-attendance'),

]