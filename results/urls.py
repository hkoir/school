
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'results'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),

    path('create_grade/', views.manage_grade, name='create_grade'),    
    path('updategrade/<int:id>/', views.manage_grade, name='update_grade'),    
    path('delete_grade/<int:id>/', views.delete_grade, name='delete_grade'),  
   
    path('create_exam_type/', views.manage_exam_type, name='create_exam_type'),    
    path('update_exam_type/<int:id>/', views.manage_exam_type, name='update_exam_type'),    
    path('delete_exam_type/<int:id>/', views.delete_exam_type, name='delete_exam_type'),  
    
    path('create_result/', views.manage_result, name='create_result'),    
    path('update_result/<int:id>/', views.manage_result, name='update_result'),    
    path('delete_result/<int:id>/', views.delete_result, name='delete_result'),  

    path('get_student_details/', views.get_student_details, name='get_student_details'),
    #path('get-subject-teacher/', views.get_subject_teacher, name='get_subject_teacher'),   
    path('get_exam_marks/', views.get_exam_marks, name='get_exam_marks'),
    path('ajax/get-exam-types/', views.get_exam_types_for_exam, name='get_exam_types'),

   path('individual_exam_result/', views.individual_exam_result, name='individual_exam_result'),
   path('aggregated_final_result/', views.aggregated_final_result, name='aggregated_final_result'),
   path('student_details_report/', views.student_details_report, name='student_details_report'),
 

   path('student_transcripts/', views.student_transcripts, name='student_transcripts'),
   path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
   path('generate_pdf/<int:id>/', views.generate_pdf, name='generate_pdf'),
   path('generate_student_pdf/', views.generate_student_pdf, name='generate_student_pdf'),

   path('GPA_Final_result_analysis/', views.GPA_Final_result_analysis, name='GPA_Final_result_analysis'),

   path('school_toppers/', views.school_toppers, name='school_toppers'),
  
 
 
  
]
