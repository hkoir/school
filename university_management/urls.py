from django.urls import path
from .views import *

app_name = 'university_management'

urlpatterns = [     
   
    path('student_enrollment', student_enrollment, name='student_enrollment'),
    path('enrollment_list/', StudentEnrollmentListView.as_view(), name='enrollment_list'),
    path('create_term_registration/<int:enrollment_id>/', term_registration_create, name='create_term_registration'),
    path('term-registration-detail/<int:student_id>/',student_term_registration_detail,name='term_registration_detail'),
    path('get_subjects_for_term/',get_subjects_for_term,name='get_subjects_for_term'),
    path('get_terms_for_level/',get_terms_for_level,name='get_terms_for_level'),

    path('invoices/', student_invoices_list, name='student_invoices_list'),
    path('invoices/<int:invoice_id>/', student_invoice_detail, name='student_invoice_detail'),
    path('payment/create/<int:invoice_id>/', university_payment_create, name='make_payment'),
    path('payment-list/', university_payment_list, name='payment_list'),

    path('exams/', exam_list, name='exam_list'),
    path('exams/create/', ExamCreateView.as_view(), name='exam_create'),
    path('exams/<int:pk>/', ExamDetailView.as_view(), name='exam_detail'),
    path('exams/<int:pk>/edit/', ExamUpdateView.as_view(), name='exam_update'),
    path('exams/<int:pk>/delete/', ExamDeleteView.as_view(), name='exam_delete'),
    path('exams/<int:exam_id>/schedule/add/', ExamScheduleCreateView.as_view(), name='exam_schedule_add'),
    path('schedule/<int:pk>/edit/', ExamScheduleUpdateView.as_view(), name='exam_schedule_update'),
    path('schedule/<int:pk>/delete/', ExamScheduleDeleteView.as_view(), name='exam_schedule_delete'),
    path('exams/schedule/create/', exam_create_with_schedule, name='exam_schedule_create'),
    path('exams/<int:pk>/publish/',exam_publish_toggle,name='exam_publish_toggle'),

    path('register_for_exam/<int:exam_id>/',register_for_exam,name='register_for_exam'),
    path('generate_admit_card/<int:exam_id>/',generate_admit_card,name='generate_admit_card'),
    path('enter_student_results/<int:exam_id>/',enter_student_results,name='enter_student_results'),
    path('student_transcript/<int:student_id>/',student_transcript,name='student_transcript'),


    path('schedule/terms/',term_list,name='term_list'),
    path('class_schedule_view/<int:term_id>/', schedule_calendar_view,name='class_schedule_view'),
    path('class_schedule_create/<int:term_id>/', class_schedule_create,name='class_schedule_create'),
    # path('student/class-schedule/<int:term_id>/',student_class_schedule,name='student_class_schedule'),
    path('teacher/class-schedule/<int:term_id>?', teacher_class_schedule,name='teacher_class_schedule_view'),

    path('common_dashboard/', common_dashboard,name='common_dashboard'),
    path('revenue_dashboard/', revenue_dashboard,name='revenue_dashboard'),


]
