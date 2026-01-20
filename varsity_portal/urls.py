from django.urls import path
from .views import *

app_name = 'varsity_portal'

urlpatterns = [  
   
    path('student_enrollment/create/', StudentEnrollmentCreateView.as_view(), name='student_enrollment_create'),
    path('student_enrollment', student_enrollment, name='student_enrollment'),
    path('enrollment_list/', student_enrollment_list, name='enrollment_list'),
    path('create_term_registration/', term_registration_create, name='create_term_registration'),
    path('term-registration-detail/',student_term_registration_detail,name='term_registration_detail'),
    path('get_subjects_for_term/',get_subjects_for_term,name='get_subjects_for_term'),
    path('get_terms_for_level/',get_terms_for_level,name='get_terms_for_level'),

    path('invoices/', student_invoices_list, name='student_invoices_list'),
    path('invoices/<int:invoice_id>/', student_invoice_detail, name='student_invoice_detail'),
   
    path('payment-list/', university_payment_list, name='payment_list'),
    path('exams/', ExamListView.as_view(), name='exam_list'),  
    path('exams/<int:pk>/', ExamDetailView.as_view(), name='exam_detail'), 

   path('term_list/',term_list,name='term_list'),
   path('class_schedule_view/<int:term_id>/',class_schedule_view,name='class_schedule_view'),
   path('student_class_schedule_view/<int:term_id>/',student_class_schedule,name='student_class_schedule'),
   path('student_class_schedule_calendar/<int:term_id>/',student_class_schedule_calendar,name='student_class_schedule_calendar'),

    path('register_for_exam/<int:exam_id>/',register_for_exam,name='register_for_exam'),
    path('generate_admit_card/<int:registration_id>/',generate_admit_card,name='generate_admit_card'),
    path('student_transcript/',student_transcript,name='student_transcript'),

    path('common_dashboard/',common_dashboard,name='common_dashboard'),
    path('view_student_vcard/', view_student_vcard,name='view_student_vcard'),
    path('student_landing_page/', student_landing_page,name='student_landing_page'),



]
