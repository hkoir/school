
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
     path('get_enrollments/<int:student_id>/', views.get_student_enrollments, name='get_student_enrollments'),
     path('get_student_data/<int:student_id>/', views.get_student_related_data, name='get_student_data'),

    path('view_student_vcard/', views.view_student_vcard, name='view_student_vcard'),
    path('student-details/<str:student_id>/', views.get_student_details, name='student-details'),

    path('student_exam_schedule/<int:student_id>/', views.student_exam_schedule, name='student_exam_schedule'),
     path('exam_schedule_view/', views.exam_schedule_view, name='exam_schedule_view'),
    path('preview_admit_card/<int:exam_id>/', views.preview_admit_card, name='preview_admit_card'),
    
    path('student_weekly_schedule/', views.student_weekly_schedule, name='student_weekly_schedule'),
    path('student_weekly_schedule_with_id<int:student_id>/', views.student_weekly_schedule_with_id, name='student_weekly_schedule_with_id'),
    path('view_student_weekly_schedule/', views.view_student_weekly_schedule, name='view_student_weekly_schedule'),


    path('exam-fees/<int:pk>/edit/', views.ExamFeeUpdateView.as_view(), name='exam_fee_edit'),
    path('exam-fees/<int:pk>/delete/', views.ExamFeeDeleteView.as_view(), name='exam_fee_delete'),

    path('transport-routes/', views.TransportRouteListView.as_view(), name='transport_route_list'),
    path('transport-routes/add/', views.TransportRouteCreateView.as_view(), name='transport_route_add'),
    path('transport-routes/<int:pk>/edit/', views.TransportRouteUpdateView.as_view(), name='transport_route_edit'),
    path('transport-routes/<int:pk>/delete/', views.TransportRouteDeleteView.as_view(), name='transport_route_delete'),
    
    path('transport-assignment-list/', views.TransportAssignmentListView.as_view(), name='transport_assignment_list'),
    path('transport-assignment/add/', views.TransportAssignmentCreateView.as_view(), name='transport_assignment_add'),
    path('transport-assignment/<int:pk>/edit/', views.TransportAssignmentUpdateView.as_view(), name='transport_assignment_edit'),
    path('transport-assignment/<int:pk>/delete/', views.TransportAssignmentDeleteView.as_view(), name='transport_assignment_delete'),

    path('hostel_room_type_list/', views.HostelRoomTypeListView.as_view(), name='hostel_room_type_list'),
    path('hostel_room_type_/add/', views.HostelRoomTypeCreateView.as_view(), name='hostel_room_type_add'),
    path('hostel_room_type_/<int:pk>/edit/', views.HostelRoomTypeUpdateView.as_view(), name='hostel_room_type_edit'),
    path('hostel_room_type_/<int:pk>/delete/', views.HostelRoomTypeDeleteView.as_view(), name='hostel_room_type_delete'),

    path('hostel_list/', views.HostelListView.as_view(), name='hostel_list'),
    path('hostel/add/', views.HostelCreateView.as_view(), name='hostel_add'),
    path('hostel/<int:pk>/edit/', views.HostelUpdateView.as_view(), name='hostel_edit'),
    path('hostel/<int:pk>/delete/', views.HostelDeleteView.as_view(), name='hostel_delete'),

    path('hostel_room_list/', views.HostelRoomlListView.as_view(), name='hostel_room_list'),  
    path('hostel_room_/add/', views.HostelRoomCreateView.as_view(), name='hostel_room_add'),
    path('hoste_rooml/<int:pk>/edit/', views.HostelRoomUpdateView.as_view(), name='hostel_room_edit'),
    path('hostel_room/<int:pk>/delete/', views.HostelRoomlDeleteView.as_view(), name='hostel_room_delete'),


    path('hostel_assignment_list/', views.HostelAssignmentlListView.as_view(), name='hostel_assignment_list'),  
    path('hostel_assignment_/add/', views.HostelAssignmentCreateView.as_view(), name='hostel_assignment_add'),
    path('hoste_assignment/<int:pk>/edit/', views.HostelAssignmentUpdateView.as_view(), name='hostel_assignment_edit'),
    path('hostel_assignment/<int:pk>/delete/', views.HostelAssignmentDeleteView.as_view(), name='hostel_assignment_delete'),
 
    path('assign_other_fee_by_class/', views.assign_other_fee_by_class, name='assign_other_fee_by_class'), 
    path('other_fees_list/', views.OtherFeesListView.as_view(), name='other_fees_list'),  
    path('other_fees__/add/', views.OtherFeesCreateView.as_view(), name='other_fees_add'),
    path('other_fees_/<int:pk>/edit/', views.OtherFeesUpdateView.as_view(), name='other_fees_edit'),
    path('other_fees_/<int:pk>/delete/', views.OtherFeesDeleteView.as_view(), name='other_fees_delete'),


    path('tuition_assignment_list/', views.TuitionAssignmentListView.as_view(), name='tuition_assignment_list'),  
    path('tuition_assignment_/add/', views.TuitionAssignmentCreateView.as_view(), name='tuition_assignment_add'),
    path('tuition_assignment/<int:pk>/edit/', views.TuitionAssignmentUpdateView.as_view(), name='tuition_assignment_edit'),
    path('tuition_assignment/<int:pk>/delete/', views.TuitionAssignmentCreateView.as_view(), name='tuition_assignment_delete'),

    path('admission_assignment_list/', views.AdmissionAssignmentListView.as_view(), name='admission_assignment_list'),  
    path('admission_assignment_/add/', views.AdmissionAssignmentCreateView.as_view(), name='admission_assignment_add'),
    path('admission_assignment/<int:pk>/edit/', views.AdmissionAssignmentUpdateView.as_view(), name='admission_assignment_edit'),
    path('admission_assignment/<int:pk>/delete/', views.AdmissionAssignmentDeleteView.as_view(), name='admission_assignment_delete'),
     
    path('student_dues_overview/', views.student_dues_overview, name='student_dues_overview'),   
    path('student_id_card_view/<int:student_id>/', views.student_id_card_view, name='student_id_card_view'),
    path('download_student_id_card/<int:student_id>/', views.download_student_id_card, name='download_student_id_card'),
    path('student_subject_enrollment_view/<int:student_id>/', views.student_subject_enrollment_view, name='student_subject_enrollment_view'),  
    path('student_id_card_print/', views.student_id_card_print, name='student_id_card_print'),

     path('student_school_class_routine_view/', views.school_class_routine_view, name='student_school_class_routine_view'),  



] 


