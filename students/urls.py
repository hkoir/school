
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'students'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),

   

    path('create_guardian/', views.manage_guardian, name='create_guardian'),    
    path('update_guardian/<int:id>/', views.manage_guardian, name='update_guardian'),    
    path('delete_guardian/<int:id>/', views.delete_guardian, name='delete_guardian'),  

    path('create_student/', views.manage_student, name='create_student'),    
    path('update_student/<int:id>/', views.manage_student, name='update_student'),    
    path('delete_student/<int:id>/', views.delete_student, name='delete_student'),  


    path('create_student_enrollment/', views.manage_student_enrollment, name='create_student_enrollment'),    
    path('update_student_enrollment/<int:id>/', views.manage_student_enrollment, name='update_student_enrollment'),    
    path('delete_student_enrollment/<int:id>/', views.delete_student_enrollment, name='delete_student_enrollment'), 

    path('get-subjects/', views.get_subjects, name='get_subjects'),
    path('enroll_student/', views.enroll_student, name='enroll_student'),

    path('view_student_vcard/', views.view_student_vcard, name='view_student_vcard'),
    path('student-details/<str:student_id>/', views.get_student_details, name='student-details'),

    path('student_exam_schedule/<int:student_id>/', views.student_exam_schedule, name='student_exam_schedule'),
    path('preview_admit_card/<int:student_id>/<int:exam_id>/', views.preview_admit_card, name='preview_admit_card'),
    

    path('student_weekly_schedule/', views.student_weekly_schedule, name='student_weekly_schedule'),
    path('student_weekly_schedule_with_id<int:student_id>/', views.student_weekly_schedule_with_id, name='student_weekly_schedule_with_id'), 
   path('view_student_weekly_schedule/', views.view_student_weekly_schedule, name='view_student_weekly_schedule'),

] 
