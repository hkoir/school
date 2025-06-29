
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'student_portal'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),
    path('attendance_report/', views.attendance_report, name='attendance_report'),    
    path('student_landing_page/', views.student_landing_page, name='student_landing_page'), 
    path('individual_exam_result/', views.individual_exam_result, name='individual_exam_result'),
    path('aggregated_final_result/', views.aggregated_final_result, name='aggregated_final_result'), 
    path('download_final_result/', views.download_final_result, name='download_final_result'), 
    path('student_exam_schedule/', views.student_exam_schedule, name='student_exam_schedule'),   
    path('preview_admit_card//<int:exam_id>/', views.preview_admit_card, name='preview_admit_card'),
    path('payment_status_view/', views.payment_status_view, name='payment_status_view'),
    path('view_notices/', views.view_notices, name='view_notices'),     
    path('class_schedule/', views.student_weekly_schedule, name='class_schedule'),



   path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:pk>/", views.inbox, name="inbox"),
    path('send-message/', views.send_message, name='send_message'),    
    path("create-group/", views.create_group_conversation, name="create_group"), 
    path('group/<int:pk>/add-participants/', views.add_participants, name='add_participants'),
    path('group/<int:pk>/remove-participants/', views.remove_participants, name='remove_participants'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),






]
