


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
    path('student_transcripts/', views.student_transcripts, name='student_transcripts'), 
    path('download_final_result/', views.download_final_result, name='download_final_result'), 
    path('exam_schedule_view/', views.exam_schedule_view, name='exam_schedule_view'),  

    path('exam_list/', views.exam_list, name='exam_list'),  
    path('preview_admit_card/<int:exam_id>/', views.preview_admit_card, name='preview_admit_card'),
    path('payment_status_view/', views.payment_status_view, name='payment_status_view'),
    path('view_notices/', views.view_notices, name='view_notices'),     

     path('class_schedule/', views.student_weekly_schedule, name='class_schedule'),   



    #path('inbox/', views.inbox, name='inbox'),
    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:pk>/", views.inbox, name="inbox"),
    path('send-message/', views.send_message, name='send_message'),    
    path("create-group/", views.create_group_conversation, name="create_group"), 
    path('group/<int:pk>/add-participants/', views.add_participants, name='add_participants'),
    path('group/<int:pk>/remove-participants/', views.remove_participants, name='remove_participants'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),


    path('choose_fee_and_generate_invoice/', views.choose_fee_and_generate_invoice, name='choose_fee_and_generate_invoice'), 
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),   
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/thank-you/<int:invoice_id>/', views.post_payment_redirect, name='post_payment_redirect'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'), 

    # new online payment method   
    path('review-and-payonline/', views.review_and_payfees_online, name='review_and_pay_online'),
    path('ssl-success/', views.ssl_success, name='ssl_success'),  
    path('ajax_pending_admission_fees/<int:student_id>/', views.ajax_pending_admission_fees, name='ajax_pending_admission_fees'),

    path('invoice/receipt/<int:pk>/', views.payment_invoice_receipt, name='payment_invoice_receipt'),
    path('payment-invoice-detail/<int:pk>/', views.payment_invoice_detail, name='payment_invoice_detail'),
    path('payment-invoice_list/', views.payment_invoice_list, name='payment_invoice_list'),

  path('view_student_vcard/', views.view_student_vcard, name='view_student_vcard'),
  path('student_dues_overview/', views.student_dues_overview, name='student_dues_overview'),   


]
