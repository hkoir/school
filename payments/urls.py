
from django.urls import path
from .views import process_payment, payment_callback

from . import views

app_name = 'payments'



urlpatterns = [

    path('create_admissionfee_policy/', views.manage_admissionfee_policy, name='create_admissionfee_policy'),    
    path('update_admissionfee_policy/<int:id>/', views.manage_admissionfee_policy, name='update_admissionfee_policy'),    
    path('delete_admissionfee_policy/<int:id>/', views.delete_admissionfee_policy, name='delete_admissionfee_policy'),  

    path('create_admissionfee/', views.manage_admissionfee, name='create_admissionfee'),    
    path('update_admissionfee/<int:id>/', views.manage_admissionfee, name='update_admissionfee'),    
    path('delete_admissionfee/<int:id>/', views.delete_admissionfee, name='delete_admissionfee'),  

    path('create_feestructure/', views.manage_feestructure, name='create_feestructure'),    
    path('update_feestructure/<int:id>/', views.manage_feestructure, name='update_feestructure'),    
    path('delete_feestructure/<int:id>/', views.delete_feestructure, name='delete_feestructure'),  


    path('create_feestructure/', views.manage_feestructure, name='create_feestructure'),    
    path('update_feestructure/<int:id>/', views.manage_feestructure, name='update_feestructure'),    
    path('delete_feestructure/<int:id>/', views.delete_feestructure, name='delete_feestructure'),  

    path("process_payment/<int:guardian_id>/", process_payment, name="process_payment"),
    path("payment/callback/", payment_callback, name="payment_callback"),
    path('bkash/ipn/', views.bkash_ipn, name="bkash_ipn"),

    path('create-placeholder-payments/', views.confirm_placeholder_creation, name='create_placeholder_payments'),
    path('ajax/get-fee-due/', views.get_fee_due_data, name='get_fee_due_data'),
    path('make-payment/search/', views.search_make_payment, name='search_make_payment'),
    path('make-payment/<str:student_id>/<int:academic_year>/', views.make_payment, name='make_payment'),

    path('choose_fee_and_make_manual_payment/', views.choose_fee_and_make_manual_payment, name='choose_fee_and_make_manual_payment'),
    path('review_manual_payment_invoice/', views.review_manual_payment_invoice, name='review_manual_payment_invoice'),
    path('finalize_manual_payment/', views.finalize_manual_payment, name='finalize_manual_payment'),

    path('payment_status_view/', views.payment_status_view, name="payment_status_view"),

    path('choose_fee_and_generate_invoice/', views.choose_fee_and_generate_invoice, name='choose_fee_and_generate_invoice'), 
    path('review_online_payment_invoice/', views.review_online_payment_invoice, name='review_online_payment_invoice'),
    path('finalize_online_payment/', views.finalize_online_payment, name='finalize_online_payment'),

    #path('choose_fee_and_make_manual_payment/', views.choose_fee_and_make_manual_payment, name="choose_fee_and_make_manual_payment"),

    path('choose_fee_and_generate_invoice/', views.choose_fee_and_generate_invoice, name='choose_fee_and_generate_invoice'), 
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),   
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/thank-you/<int:invoice_id>/', views.post_payment_redirect, name='post_payment_redirect'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'), 




]
