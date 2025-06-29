from django.shortcuts import render,redirect
from decimal import Decimal
from django.contrib import messages
from .forms import FeeStructureForm

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from students.models import Student,Guardian
from.models import FeeStructure
from messaging.models import Message
import requests
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Payment
from calendar import month_name
from datetime import date
from django.db.models import Sum
from attendance.forms import AttendanceFilterForm
from collections import Counter



from.models import AdmissionFee,AdmissionFeePolicy
from.forms import AdmissionfeeForm,AdmissionfeePolicyForm



from.forms import PaymentForm
from .forms import PaymentSearchForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import FeePaymentForm
from .models import PaymentInvoice, Payment
from students.models import Student
from django.conf import settings
from django.http import HttpResponse
from payment_gatway.models import TenantPaymentConfig



@login_required
def manage_admissionfee_policy(request, id=None):   
    instance = get_object_or_404(AdmissionFeePolicy, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AdmissionfeePolicyForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AdmissionfeePolicyForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('payments:create_admissionfee_policy')  
        else:
            print(form.errors) 

    datas = AdmissionFeePolicy.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
   
    return render(request, 'payments/manage_admissionfee_policy.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })




@login_required
def delete_admissionfee_policy(request, id):
    instance = get_object_or_404(AdmissionFeePolicy, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('payments:create_admissionfee_policy')    

    messages.warning(request, "Invalid delete request!")
    return redirect('payments:create_admissionfee_policy')   





@login_required
def manage_admissionfee(request, id=None):   
    instance = get_object_or_404(AdmissionFee, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AdmissionfeeForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AdmissionfeeForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('payments:create_admissionfee')  
        else:
            print(form.errors) 

    datas = AdmissionFee.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
   
    return render(request, 'payments/manage_admissionfee.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })




@login_required
def delete_admissionfee(request, id):
    instance = get_object_or_404(AdmissionFee, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('payments:create_admissionfee')    

    messages.warning(request, "Invalid delete request!")
    return redirect('payments:create_admissionfee')   







@login_required
def manage_feestructure(request, id=None):   
    instance = get_object_or_404(FeeStructure, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = FeeStructureForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('payments:create_feestructure')  
        else:
            print(form.errors) 

    datas = FeeStructure.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
   
    return render(request, 'payments/manage_feestructure.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })




@login_required
def delete_feestructure(request, id):
    instance = get_object_or_404(FeeStructure, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('payments:create_feestructure')    

    messages.warning(request, "Invalid delete request!")
    return redirect('payments:create_feestructure')   




from payment_gatway.models import TenantPaymentConfig



def get_payment_gateway(student, provider_name):
    tenant = student.user.tenant
    return TenantPaymentConfig.objects.filter(
        tenant=tenant,
        payment_system__method=provider_name 
    ).first()



def process_payment(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        amount_paid = Decimal(request.POST.get("amount_paid"))
        payment_method = request.POST.get("payment_method")  

        try:
            student = Student.objects.get(id=student_id)
            guardian = student.guardian
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect('payment_form')

        gateway_config = get_payment_gateway(student, payment_method)

        if not gateway_config:
            messages.error(request, "Payment configuration not found for this provider.")
            return redirect('payment_form')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gateway_config.api_key}"
        }

        data = {
            "amount": str(amount_paid),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": f"INV-{guardian.id}-{student.id}",
            "callbackURL": gateway_config.payment_redirect_url or request.build_absolute_uri("/payment/callback/")
        }

        response = requests.post(
            url=gateway_config.payment_system.base_url,  
            json=data,
            headers=headers
        )

        if response.status_code == 200:
            payment_data = response.json()
            if "bkashURL" in payment_data:
                return redirect(payment_data["bkashURL"])
            else:
                messages.error(request, "bKash did not return a valid payment URL.")
        else:
            messages.error(request, f"Payment initiation failed: {response.text}")

    return redirect('payments:payment_form')







def payment_callback(request):  
    data = request.GET  
    transaction_id = data.get("paymentID")
    status = data.get("status")
    paid_amount = Decimal(data.get("amount"))
    invoice_number = data.get("merchantInvoiceNumber")

    parts = invoice_number.split("-")
    guardian_id = parts[1]
    student_id = parts[2]

    guardian = get_object_or_404(Guardian, id=guardian_id)
    student = get_object_or_404(Student, id=student_id)


    if status == "Completed":
        unpaid_records = Payment.objects.filter(student=student, payment_status='due').order_by('due_date')
        remaining_amount = paid_amount
        for record in unpaid_records:
            if remaining_amount >= record.due_amount:
                remaining_amount -= record.due_amount
                record.amount_paid = record.due_amount  
                record.payment_status = 'paid'
                record.due_amount = 0
            else:
                record.amount_paid += remaining_amount
                record.due_amount -= remaining_amount
                record.payment_status = 'partial-paid'
                remaining_amount = 0
            record.save()
            if remaining_amount == 0:
                break

        remaining_due = sum(record.remaining_due for record in Payment.objects.filter(student=student, is_paid=False))
        message_content = f"Dear {guardian.name}, your payment of ${paid_amount} has been received. Remaining due: ${remaining_due}."

        msg = Message.objects.create(
            student=student,
            guardian=guardian,
            message_content=message_content,
            message_type="Fee"
        )
        msg.send_sms()

        return JsonResponse({"message": "Payment verified and updated successfully."})

    else:
        return JsonResponse({"error": "Payment failed or not completed."}, status=400)




from django.http import HttpResponse

@login_required
def send_fee_payment_sms(request, amount):
    student = Student.objects.filter(user=request.user).first()
    
    if not student:
        return HttpResponse("Student not found", status=404)

    guardian = student.guardian 
    if not guardian:
        return HttpResponse("Guardian not found", status=404)

    message_content = f"Dear {guardian.name}, your child {student.first_name} has made a payment of {amount} for tuition fees."

    message = Message.objects.create(
        user=request.user,
        student=student,
        guardian=guardian,
        message_content=message_content,
        message_type="Fee"
    )

    message.send_sms()
    return HttpResponse("SMS sent successfully")









def calculate_total_due(student):
    unpaid_records = Payment.objects.filter(student=student, payment_status ='due')
    return sum(record.fee_amount for record in unpaid_records)




def get_due_months(student):
    unpaid_records = Payment.objects.filter(student=student, payment_status = 'due').order_by('due_date')    
    due_months = [record.due_date.strftime('%B %Y') for record in unpaid_records]
    return due_months




def send_payment_confirmation_sms(guardian, amount, method, transaction_id):
    message_content = f"Dear {guardian.name}, we have received BDT {amount} via {method}. Transaction ID: {transaction_id}. Thank you!"

    Message.objects.create(
        student=guardian.student,
        guardian=guardian,
        message_content=message_content,
        message_type="Fee",
        is_sent=True  # Mark as sent
    )

    send_sms(guardian.phone_number, message_content)  # Call SMS API




def send_sms(phone_number, message):
    url = "https://smsprovider.com/api/send"
    payload = {"phone": phone_number, "message": message, "api_key": "YOUR_SMS_API_KEY"}
    
    response = requests.post(url, json=payload)
    return response.json()



################### payment from bikash mobile apps ###################################################

# Register an IPN URL with bKash
# You need to provide bKash with an API endpoint where they will send payment notifications.
# Example URL: https://yourwebsite.com/bkash/ipn/
# Create an API Endpoint in Django
# This will receive payment details from bKash.




@csrf_exempt
def bkash_ipn(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            transaction_id = data.get("trxID")
            amount = data.get("amount")
            reference = data.get("reference")
            status = data.get("transactionStatus")

            if status == "Completed":
                # Extract student ID from reference
                student_id, month = reference.split("-")  # Example: "12345-AUG"
                student = Student.objects.get(id=student_id)

                # Mark payment as completed in database
                Payment.objects.create(
                    student=student,
                    amount=amount,
                    month=month,
                    transaction_id=transaction_id,
                    is_paid=True
                )

                return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "invalid request"}, status=400)






def get_total_admission_fee(student):
    enrollment = student.enrolled_students.first()
    if not enrollment or not enrollment.feestructure:
        return Decimal('0.00')     

    admission_fee_policy = enrollment.feestructure.admissionfee_policy
    if not admission_fee_policy or admission_fee_policy.total_admission_fee is None:
        return Decimal('0.00')   

    return admission_fee_policy.total_admission_fee




def get_total_admission_fee_paid(student):
    enrollment = student.enrolled_students.first()
    if not enrollment:
        return Decimal('0.00')
    academic_year = enrollment.academic_year
    total_paid = AdmissionFeePayment.objects.filter(
        payment__student=student,
        payment__academic_year=academic_year
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    return total_paid




def get_student_due_status(student):
    admission_status ='None'
    enrollment = student.enrolled_students.first()
    academic_year = student.enrolled_students.first().academic_year
    language_version = student.enrolled_students.first().student_class.language_version
    monthly_status = {}

    if not enrollment or not enrollment.feestructure:
        monthly_status = {month: 'unknown' for month in range(1, 13)}
        return {
            'monthly_status': monthly_status,
            'admission_status': 'not-applicable',
        }

    feestructure = enrollment.feestructure
    expected_monthly_fee = feestructure.monthly_tuition_fee

    # ========== Monthly Tuition Fee Status ========== #
    current_month = date.today().month
    for month in range(1, current_month + 1):
        paid = Payment.objects.filter(
            student=student,
            academic_year=academic_year,
            month=month
        ).aggregate(total=Sum('monthly_tuition_fee_paid'))['total'] or Decimal(0.00)

        if paid >= expected_monthly_fee:
            monthly_status[month] = 'paid'
        elif paid > 0:
            monthly_status[month] = 'partial-paid'
        else:
            monthly_status[month] = 'due'

    # ========== Admission Fee Status ========== #
    total_fee = get_total_admission_fee(student)
    total_paid = get_total_admission_fee_paid(student)

    # Handle cases where admission fee is not applicable
    if total_fee == 0:
        admission_status = 'not-applicable'
    elif total_paid >= total_fee:
        admission_status = 'paid'
    elif total_paid > 0:
        admission_status = 'partial-paid'
    else:
        admission_status = 'due'

    return {
        'monthly_status': monthly_status,
        'admission_status': admission_status,
    }





def calculate_due_and_paid(student):
    total_due_amount = None
    total_paid_amount = None
    today = date.today()
    current_month = today.month
    enrollment = student.enrolled_students.first()
    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year
    if fee_structure:
    	monthly_fee = fee_structure.monthly_tuition_fee
    	total_due_amount = monthly_fee * current_month
    total_paid_amount = student.student_payments.filter(academic_year=academic_year).aggregate(
        total_paid=Sum('monthly_tuition_fee_paid')
    )['total_paid'] or 0
    return total_due_amount, total_paid_amount





def payment_status_view(request):
    form = AttendanceFilterForm(request.GET or None) 
    students = Student.objects.none()   
    class_name = None
    section = None
    subject = None
    shift = None
    version = None
    class_gender = None
    academic_year=None
    total_due_amount = Decimal('0.00')
    total_paid_amount = Decimal('0.00')
    data = []
    months = [date(1900, i, 1).strftime('%B') for i in range(1, 13)]
    payment_status_data =[] 
   
    if request.method == 'GET' and form.is_valid():     
       
        class_name = form.cleaned_data.get("class_name")
        section = form.cleaned_data.get("section")    
        academic_year = form.cleaned_data.get("academic_year")   
        subject = form.cleaned_data.get("subject")  
        shift = form.cleaned_data.get("shift")    
        class_gender = form.cleaned_data.get("class_gender")   
        language_version = form.cleaned_data.get("version") 
        student = form.cleaned_data.get("student") 

        students = Student.objects.all()      

        if academic_year:
            students = students.filter(enrolled_students__academic_year=academic_year)       
        if class_name:
            students = students.filter(enrolled_students__student_class=class_name)           
        if section:
            students = students.filter(enrolled_students__section=section)          
        if shift and shift not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__shift=shift)          
        if class_gender and class_gender not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__section__class_gender=class_gender)         
        if language_version and language_version not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__language_version=language_version)          
        if subject:
            students = students.filter(enrolled_students__subjects__in=[subject])           
        if student:
            students = students.filter(id=student.id)
              
        total_student = students.count()
        total_due_amount = Decimal('0.00')
        total_paid_amount = Decimal('0.00')
        for student in students:          
            fee_status = get_student_due_status(student)
            total_due, total_paid = calculate_due_and_paid(student)	    
            total_due = total_due or Decimal('0.00')
            total_paid = total_paid or Decimal('0.00')           
            total_due_amount += total_due
            total_paid_amount += total_paid

            data.append({
                'student': student,             
                'status_by_month': fee_status['monthly_status'],
                'admission_status': fee_status.get('admission_status', 'not-set'),
              
            })

        status_counts = Counter([row['admission_status'] for row in data])
        total_paid = status_counts.get('paid', 0)
        total_partial = status_counts.get('partial-paid', 0)
        total_due = status_counts.get('due', 0)
        total_not_applicable = status_counts.get('not-applicable', 0)
       
        # for chart data preparation
        payment_status_data = {
            #admission fee
            'total_paid': total_paid,
            'total_partial': total_partial,
            'total_due': total_due,
            'total_not_applicable': total_not_applicable,

            # Monthly tution fee
            'total_due_amount': float(total_due_amount), 
            'total_paid_amount': float(total_paid_amount),
            'total_student':total_student
        }

     
    context = {
            'data': data,
            'months':months,
            'payment_status_data': json.dumps(payment_status_data), 
            'form':form
        }
    return render(request, 'payments/payment_status.html', context)




#=============================================================================
from django.utils import timezone
from.forms import PaymentForm
from .forms import PaymentSearchForm

def create_placeholder_payments_for_all_students(request):
    months_in_academic_year = list(range(4, 13)) + list(range(1, 4))  
    students = Student.objects.all()
    current_month = timezone.now().month

    for student in students:
        for month in months_in_academic_year:
            payment_exists = Payment.objects.filter(
                student=student,
                academic_year=timezone.now().year,
                month=month
            ).exists()

            if not payment_exists:
                monthly_tuition_fee = student.enrolled_students.first().feestructure.monthly_tuition_fee             
                payment_status = 'due' if month <= current_month else None  

                p = Payment(
                    student=student,
                    academic_year=timezone.now().year,
                    month=month,
                    due_date=timezone.datetime(timezone.now().year, month, 25),
                    payment_status=payment_status, 
                    total_paid=0,
                    remaining_due=monthly_tuition_fee
                )
                p.save() 
    messages.success(request, "Placeholder payments have been created successfully.")
    return redirect('core:dashboard')


@login_required
def confirm_placeholder_creation(request):
    if request.method == "POST":
        return create_placeholder_payments_for_all_students(request)
    return render(request, 'payments/confirm_placeholder.html')



# ajax call for dynamic update
def get_fee_due_data(request):
    student_id = request.GET.get('student_id')
    academic_year = request.GET.get('academic_year')
    selected_month = request.GET.get('month')
    try:
        student = Student.objects.get(student_id=student_id)
        academic_year = int(academic_year)
        selected_month = int(selected_month)
        today = date.today()
        current_month = today.month    
        if today.day < 25:
            max_month = current_month - 1
        else:
            max_month = current_month
        countable_month = min(selected_month, max_month)
        enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
        monthly_due = Decimal('0.00')
        admission_due = Decimal('0.00')

        if enrollment and enrollment.feestructure:
            monthly_fee = enrollment.feestructure.monthly_tuition_fee or Decimal('0.00')
            total_expected_tuition = monthly_fee * countable_month

            total_paid_tuition = Payment.objects.filter(
                student=student,
                academic_year=academic_year,
                month__lte=countable_month
            ).aggregate(total=Sum('monthly_tuition_fee_paid'))['total'] or Decimal('0.00')

            monthly_due = max(total_expected_tuition - total_paid_tuition, Decimal('0.00'))
            policy = enrollment.feestructure.admissionfee_policy
            if policy:
                admission_total_due = sum(
                    fee.amount for fee in policy.admission_fees.filter(due_month__lte=countable_month)
                )
                admission_paid = Payment.objects.filter(
                    student=student,
                    academic_year=academic_year
                ).aggregate(total=Sum('admission_fee_paid'))['total'] or Decimal('0.00')

                admission_due = max(admission_total_due - admission_paid, Decimal('0.00'))

        return JsonResponse({
            'monthly_due': float(monthly_due),
            'admission_due': float(admission_due),
        })

    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@login_required
def search_make_payment(request):
    form = PaymentSearchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        student_id = form.cleaned_data['student_id'].strip()
        academic_year = form.cleaned_data['academic_year']
        try:
            student = Student.objects.get(student_id=student_id)    
            return redirect('payments:make_payment', student_id=student.student_id, academic_year=academic_year)
        except Student.DoesNotExist:
            messages.error(request, "No student found with that Student ID.")
    return render(request, 'payments/make_payment_search.html', {'form': form})



@login_required
def make_payment(request, student_id, academic_year):
    student = get_object_or_404(Student, student_id=student_id)
    form = PaymentForm(request.POST or None, student=student)

    if form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        monthly_amount = form.cleaned_data['monthly_tuition_fee_paid'] or 0
        admission_paid_amount = form.cleaned_data.get('admission_fee_paid') or 0

        # Process monthly tuition fee payments
        unpaid_months = Payment.objects.filter(
            student=student,
            academic_year=academic_year
        ).exclude(payment_status='Paid').order_by('month')

        for payment in unpaid_months:
            due_amount = payment.get_monthly_due_amount()
            if monthly_amount >= due_amount:
                payment.monthly_tuition_fee_paid = (payment.monthly_tuition_fee_paid or 0) + due_amount
                payment.payment_status = 'Paid'
                monthly_amount -= due_amount
            else:
                payment.monthly_tuition_fee_paid = (payment.monthly_tuition_fee_paid or 0) + monthly_amount
                payment.payment_status = 'Partial'
                monthly_amount = 0

            payment.save()
            if monthly_amount <= 0:
                break

        # Process admission fee payment
        if admission_paid_amount > 0:
            existing_admission_payment = Payment.objects.filter(
                student=student,
                academic_year=academic_year
            ).aggregate(total=Sum('admission_fee_paid'))['total'] or 0

            enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
            admission_policy = enrollment.feestructure.admissionfee_policy if enrollment and enrollment.feestructure else None

            if admission_policy:
                total_admission_fee = admission_policy.admission_fees.aggregate(total=Sum('amount'))['total'] or 0
                remaining_admission_due = total_admission_fee - existing_admission_payment
                applied_admission_payment = min(admission_paid_amount, remaining_admission_due)

                # Add admission fee to current month's payment
                current_month = date.today().month
                payment_for_current_month = Payment.objects.filter(
                    student=student,
                    academic_year=academic_year,
                    month=current_month
                ).first()

                if payment_for_current_month:
                    payment_for_current_month.admission_fee_paid = (
                        payment_for_current_month.admission_fee_paid or 0
                    ) + applied_admission_payment
                    payment_for_current_month.save()
                else:
                    # Create new payment record for current month if none exists
                    Payment.objects.create(
                        student=student,
                        academic_year=academic_year,
                        month=current_month,
                        admission_fee_paid=applied_admission_payment,
                        payment_status='Partial',
                        due_date=timezone.datetime(timezone.now().year, current_month, 25),
                        total_paid=0.00,
                        remaining_due=0.00
                    )

        messages.success(request, "Payment successfully processed.")
        return redirect('payments:search_make_payment')

    return render(request, 'payments/make_payment.html', {
        'form': form,
        'student': student
    })

#===================================== Manual payment final view =========================================


from .forms import ManualPaymentForm
@login_required
def choose_fee_and_make_manual_payment(request):
    today = date.today()
    current_month = today.month

    # Student selection logic stays unchanged...
    student_id = request.GET.get('student_id')
    if student_id:
        student = Student.objects.filter(student_id=student_id).first()
        if not student:
            messages.error(request, "No student found with the provided Student ID.")
            return render(request, 'payments/select_student.html', {'student_select_form': StudentSelectForm()})
    elif request.user.is_authenticated:
        student = Student.objects.filter(user=request.user).first()

    if not student:
        student_select_form = StudentSelectForm(request.POST or None)
        if request.method == 'POST' and student_select_form.is_valid():
            selected = student_select_form.cleaned_data.get('student')
            entered_id = student_select_form.cleaned_data.get('student_id_input')
            if selected:
                return redirect(f"{request.path}?student_id={selected.student_id}")
            elif entered_id:
                return redirect(f"{request.path}?student_id={entered_id}")
        return render(request, 'payments/select_student.html', {'student_select_form': student_select_form})

    enrollment = student.enrolled_students.order_by('-academic_year').first()
    if not enrollment or not enrollment.feestructure:
        messages.warning(request, 'No fee structure defined for this student.')
        return redirect('payments:search_make_payment')

    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year

    paid_months = Payment.objects.filter(
        student=student,
        academic_year=academic_year,
        monthly_tuition_fee_payment_status='paid'
    ).exclude(month__isnull=True).values_list('month', flat=True)

    unpaid_months = [m for m in range(1, 13) if m not in paid_months]
    all_unpaid_choices = [(m, date(1900, m, 1).strftime('%B')) for m in unpaid_months]

    due_cutoff_month = current_month if today.day >= 25 else current_month - 1
    due_months = [m for m in unpaid_months if m <= due_cutoff_month]
    tuition_due_total = fee_structure.monthly_tuition_fee * len(due_months)

    all_adm_items = AdmissionFee.objects.filter(admission_fee_policy=fee_structure.admissionfee_policy)
    paid_item_ids = AdmissionFeePayment.objects.filter(payment__student=student).values_list('admission_fee_item_id', flat=True)
    unpaid_adm_items = all_adm_items.exclude(id__in=paid_item_ids)

    admission_due_items = unpaid_adm_items.filter(due_month__lte=due_cutoff_month)
    admission_due_total = sum(item.amount for item in admission_due_items)

    if request.method == 'POST':
        form = ManualPaymentForm(request.POST, student=student)
        form.fields['tuition_months'].choices = all_unpaid_choices
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

        if form.is_valid():
            selected_months = form.cleaned_data.get('tuition_months', [])
            selected_fees = form.cleaned_data.get('admission_fee_items', [])

            # 🔁 Save to session, not DB
            request.session['manual_payment_data'] = {
                'student_id': student.student_id,
                'selected_months': selected_months,
                'selected_admission_fee_ids': [item.id for item in selected_fees],
            }

            # ✅ Redirect to review (Step 2)
            return redirect('payments:review_manual_payment_invoice')
    else:
        form = ManualPaymentForm(student=student)
        form.fields['tuition_months'].choices = all_unpaid_choices
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

    return render(request, 'payments/select_fee_type_manual.html', {
        'form': form,
        'student': student,
        'tuition_due_total': tuition_due_total,
        'admission_due_total': admission_due_total,
        'current_month': current_month,
    })








@login_required
def review_manual_payment_invoice(request):
    today = date.today()
    current_month = today.month

    # Same student lookup logic as before...
    student = None
    student_id = request.GET.get('student_id')
    if student_id:
        student = Student.objects.filter(student_id=student_id).first()
    elif request.user.is_authenticated:
        student = Student.objects.filter(user=request.user).first()

    if not student:
        student_select_form = StudentSelectForm(request.POST or None)
        if request.method == 'POST' and student_select_form.is_valid():
            selected = student_select_form.cleaned_data.get('student')
            entered_id = student_select_form.cleaned_data.get('student_id_input')
            if selected:
                return redirect(f"{request.path}?student_id={selected.student_id}")
            elif entered_id:
                return redirect(f"{request.path}?student_id={entered_id}")
        return render(request, 'payments/select_student.html', {'student_select_form': student_select_form})

    enrollment = student.enrolled_students.order_by('-academic_year').first()
    if not enrollment or not enrollment.feestructure:
        messages.warning(request, 'No fee structure defined for this student.')
        return redirect('payments:search_make_payment')

    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year

    paid_months = Payment.objects.filter(
        student=student,
        academic_year=academic_year,
        monthly_tuition_fee_payment_status='paid'
    ).exclude(month__isnull=True).values_list('month', flat=True)

    unpaid_months = [m for m in range(1, 13) if m not in paid_months]
    all_unpaid_choices = [(m, date(1900, m, 1).strftime('%B')) for m in unpaid_months]

    due_cutoff_month = current_month if today.day >= 25 else current_month - 1
    due_months = [m for m in unpaid_months if m <= due_cutoff_month]

    all_adm_items = AdmissionFee.objects.filter(admission_fee_policy=fee_structure.admissionfee_policy)
    paid_item_ids = AdmissionFeePayment.objects.filter(payment__student=student).values_list('admission_fee_item_id', flat=True)
    unpaid_adm_items = all_adm_items.exclude(id__in=paid_item_ids)

    if request.method == 'POST':
        form = ManualPaymentForm(request.POST, student=student)
        form.fields['tuition_months'].choices = all_unpaid_choices
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

        if form.is_valid():
            selected_months = form.cleaned_data['tuition_months']
            selected_fees = form.cleaned_data['admission_fee_items']

            preview_data = {
                'student': student,
                'form': form,
                'selected_months': selected_months,
                'selected_month_names': [date(1900, int(m), 1).strftime('%B') for m in selected_months],
                'selected_admission_fees': selected_fees,
                'tuition_fee_total': fee_structure.monthly_tuition_fee * len(selected_months),
                'admission_fee_total': sum(item.amount for item in selected_fees),
                'current_month': current_month,
            }

            request.session['manual_payment_data'] = {
                'student_id': student.student_id,
                'selected_months': selected_months,
                'selected_admission_fee_ids': [item.id for item in selected_fees],
            }

            return render(request, 'payments/review_invoice.html', preview_data)
    else:
        form = ManualPaymentForm(student=student)
        form.fields['tuition_months'].choices = all_unpaid_choices
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

    return render(request, 'payments/select_fee_type_manual.html', {
        'form': form,
        'student': student,
        'tuition_due_total': fee_structure.monthly_tuition_fee * len(due_months),
        'admission_due_total': sum(item.amount for item in unpaid_adm_items.filter(due_month__lte=due_cutoff_month)),
        'current_month': current_month,
    })




@login_required
def finalize_manual_payment(request):
    data = request.session.get('manual_payment_data')
    if not data:
        messages.error(request, "No payment data found.")
        return redirect('payments:choose_fee_and_make_manual_payment')

    student = Student.objects.filter(student_id=data['student_id']).first()
    if not student:
        messages.error(request, "Student not found.")
        return redirect('payments:choose_fee_and_make_manual_payment')

    enrollment = student.enrolled_students.order_by('-academic_year').first()
    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year
    today = date.today()
    current_month = today.month

    for month in data['selected_months']:
        payment, _ = Payment.objects.get_or_create(
            student=student,
            academic_year=academic_year,
            month=month,
            defaults={
                'due_date': timezone.datetime(today.year, int(month), 25),
                'monthly_tuition_fee_paid': 0,
                'total_paid': 0,
                'remaining_due': 0,
                'payment_status': 'Partial',
            }
        )
        payment.monthly_tuition_fee_paid = fee_structure.monthly_tuition_fee
        payment.save()

    selected_fee_items = AdmissionFee.objects.filter(id__in=data['selected_admission_fee_ids'])
    if selected_fee_items.exists():
        current_month_payment, _ = Payment.objects.get_or_create(
            student=student,
            academic_year=academic_year,
            month=current_month,
            defaults={
                'due_date': timezone.datetime(today.year, current_month, 25),
                'total_paid': 0,
                'remaining_due': 0,
                'payment_status': 'Partial',
            }
        )
        current_month_payment.admission_fee_paid = (
            current_month_payment.admission_fee_paid or Decimal(0.00)
        ) + sum(item.amount for item in selected_fee_items)
        current_month_payment.save()

        for item in selected_fee_items:
            AdmissionFeePayment.objects.create(
                payment=current_month_payment,
                admission_fee_item=item
            )

    del request.session['manual_payment_data']
    messages.success(request, "Manual payment successfully recorded.")
    return redirect('payments:search_make_payment')



#====================== online payment ========================================================



from .forms import FeePaymentForm, StudentSelectForm 
from datetime import date
today = date.today()
current_month_number = today.month
current_month = today.month




@login_required
def choose_fee_and_generate_invoice(request):
    today = date.today()
    current_month = today.month

    student = None
    student_select_form = None

    student_id = request.GET.get('student_id')
    if student_id:
        student = Student.objects.filter(student_id=student_id).first()
        if not student:
            messages.error(request, "No student found with the provided Student ID.")
            return render(request, 'payments/select_student.html', {'student_select_form': StudentSelectForm()})
    elif request.user.is_authenticated:
        student = Student.objects.filter(user=request.user).first()

    if not student:
        student_select_form = StudentSelectForm(request.POST or None)
        if request.method == 'POST' and student_select_form.is_valid():
            selected = student_select_form.cleaned_data.get('student')
            entered_id = student_select_form.cleaned_data.get('student_id_input')
            if selected:
                return redirect(f"{request.path}?student_id={selected.student_id}")
            elif entered_id:
                return redirect(f"{request.path}?student_id={entered_id}")
        return render(request, 'payments/select_student.html', {'student_select_form': student_select_form})

    enrollment = student.enrolled_students.order_by('-academic_year').first()
    if not enrollment or not enrollment.feestructure:
        messages.warning(request, 'No fee structure defined for this student.')
        return redirect('payments:payment_status_view')

    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year

    paid_months = Payment.objects.filter(
        student=student,
        academic_year=academic_year,
        monthly_tuition_fee_payment_status='paid'
    ).exclude(month__isnull=True).values_list('month', flat=True)

    unpaid_months = [m for m in range(1, 13) if m not in paid_months]
    due_months_choices = [(m, date(1900, m, 1).strftime('%B')) for m in unpaid_months if m <= current_month]
    all_unpaid_choices = [(m, date(1900, m, 1).strftime('%B')) for m in unpaid_months]

    all_adm_items = AdmissionFee.objects.filter(admission_fee_policy=fee_structure.admissionfee_policy)
    paid_item_ids = AdmissionFeePayment.objects.filter(payment__student=student).values_list('admission_fee_item_id', flat=True)
    unpaid_adm_items = all_adm_items.exclude(id__in=paid_item_ids)
    due_admission_fee_items = unpaid_adm_items.filter(due_month__lte=current_month)

    if request.method == 'POST':
        form = FeePaymentForm(request.POST, student=student, tuition_months_choices=all_unpaid_choices)
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

        if form.is_valid():
            request.session['online_payment_data'] = {
                'student_id': student.student_id,
                'selected_months': form.cleaned_data.get('tuition_months', []),
                'selected_admission_fee_ids': [f.id for f in form.cleaned_data.get('admission_fee_items', [])],
                'fee_types': form.cleaned_data.get('fee_types'),
            }
            return redirect('payments:review_online_payment_invoice')
    else:
        form = FeePaymentForm(student=student, tuition_months_choices=all_unpaid_choices)
        form.fields['admission_fee_items'].queryset = unpaid_adm_items

    return render(request, 'payments/select_fee_type.html', {
        'form': form,
        'student': student,
        'tuition_due_total': fee_structure.monthly_tuition_fee * len(due_months_choices),
        'admission_due_total': sum(item.amount for item in due_admission_fee_items),
        'current_month': current_month,
    })




@login_required
def review_online_payment_invoice(request):
    data = request.session.get('online_payment_data')
    if not data:
        messages.error(request, "No payment data found.")
        return redirect('payments:choose_fee_and_generate_invoice')

    student = get_object_or_404(Student, student_id=data['student_id'])
    enrollment = student.enrolled_students.order_by('-academic_year').first()
    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year

    selected_months = data['selected_months']
    selected_admission_fees = AdmissionFee.objects.filter(id__in=data['selected_admission_fee_ids'])
    selected_month_names = [date(1900, int(m), 1).strftime('%B') for m in selected_months]

    context = {
        'student': student,
        'selected_months': selected_months,
        'selected_month_names': selected_month_names,
        'selected_admission_fees': selected_admission_fees,
        'tuition_fee_total': fee_structure.monthly_tuition_fee * len(selected_months),
        'admission_fee_total': sum(f.amount for f in selected_admission_fees),
        'current_month': date.today().month,
    }
    return render(request, 'payments/review_invoice_online.html', context)




@login_required
def finalize_online_payment(request):
    data = request.session.get('online_payment_data')
    if not data:
        messages.error(request, "No payment data found.")
        return redirect('payments:choose_fee_and_generate_invoice')

    student = get_object_or_404(Student, student_id=data['student_id'])
    enrollment = student.enrolled_students.order_by('-academic_year').first()
    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year

    total_amount = fee_structure.monthly_tuition_fee * len(data['selected_months']) + \
                   sum(AdmissionFee.objects.filter(id__in=data['selected_admission_fee_ids']).values_list('amount', flat=True))

    description_parts = []
    if data['selected_months']:
        months_display = ", ".join([date(1900, int(m), 1).strftime('%B') for m in data['selected_months']])
        description_parts.append(f"Tuition Fee for {months_display} {academic_year}")

    if data['selected_admission_fee_ids']:
        admission_names = ", ".join(
            AdmissionFee.objects.filter(id__in=data['selected_admission_fee_ids']).values_list('fee_type', flat=True)
        )
        description_parts.append(f"Admission Fee: {admission_names}")

    invoice = PaymentInvoice.objects.create(
        student=student,
        invoice_type='combined',
        amount=total_amount,
        description='; '.join(description_parts),
        extra_data={'tuition_months': data['selected_months']}
    )
    invoice.admission_fee_items.set(data['selected_admission_fee_ids'])

    del request.session['online_payment_data']
    return redirect(f"/payments/payment/initiate/?tran_id={invoice.tran_id}")




from payment_gatway.models import PaymentSystem


def initiate_payment(request):
    client = request.tenant    
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    try:
        sslcommerz = PaymentSystem.objects.get(method='sslcommerz')
        config = TenantPaymentConfig.objects.get(tenant=client, payment_system=sslcommerz)
    except (PaymentSystem.DoesNotExist, TenantPaymentConfig.DoesNotExist):
        messages.error(request, "SSLCommerz is not configured for this tenant.")
        return redirect('payments:payment_status_view')
    
    if not tran_id:
        return HttpResponse("Missing transaction ID.")
    
    store_id = config.client_id or config.merchant_id  
    store_pass = config.client_secret or config.api_key
    #base_url = sslcommerz.base_url or "https://sandbox.sslcommerz.com"  # fallback
    base_url = config.get_payment_url() or "https://sandbox.sslcommerz.com"

    invoice = get_object_or_404(PaymentInvoice, tran_id=tran_id)
    student = invoice.student
    enrollment = student.enrolled_students.filter(academic_year=invoice.created_at.year).first()

    post_data = {
        'store_id': store_id,
        'store_passwd': store_pass,
        'total_amount': invoice.amount,
        'currency': "BDT",
        'tran_id': invoice.tran_id,
        'success_url': request.build_absolute_uri('/payments/payment/success/'),
        'fail_url': request.build_absolute_uri('/payments/payment/fail/'),
        'cancel_url': request.build_absolute_uri('/payments/payment/cancel/'),

        'emi_option': 0,
        'cus_name': student.name,
        'cus_email': student.user.email or "info@example.com",
        'cus_phone': student.phone_number or "017xxxxxxxx",
        'cus_add1': "Dhaka",
        'cus_city': "Dhaka",
        'cus_country': "Bangladesh",
        'shipping_method': "NO",
        'product_name': invoice.description or invoice.invoice_type,
        'product_category': "Education",
        'product_profile': "general",

        'value_a': str(invoice.pk),
        'value_b': str(invoice.tuition_month) if invoice.invoice_type == "tuition_fees" else '',
    }

    url = f"{base_url.rstrip('/')}/gwprocess/v4/api.php"


    response = requests.post(url, data=post_data)
    data = response.json()

    if data.get('status') == "SUCCESS":
        return redirect(data['GatewayPageURL'])
    return HttpResponse("Payment failed: " + data.get('failedreason', 'Unknown'))



from.models import AdmissionFeePayment





@csrf_exempt
def payment_success(request):
    if request.method != "POST":
        return HttpResponse("Invalid access")

    tran_id = request.POST.get("tran_id")
    if not tran_id:
        return HttpResponse("Transaction ID missing.")

    invoice = get_object_or_404(PaymentInvoice, tran_id=tran_id)
    student = invoice.student
    enrollment = student.enrolled_students.filter(academic_year=invoice.created_at.year).first()

    if not enrollment:
        return HttpResponse("Enrollment not found for this student.")
    
    extra_data = invoice.extra_data or {}
    tuition_months = extra_data.get('tuition_months', [])

    # Process Tuition Payments
    if tuition_months:
        for month in tuition_months:
            payment, _ = Payment.objects.get_or_create(
                academic_year=enrollment.academic_year,
                student=student,
                month=int(month)
            )
            payment.monthly_tuition_fee_paid = enrollment.feestructure.monthly_tuition_fee
            payment.monthly_tuition_fee_payment_status = "paid"
            payment.payment_method = "sslcommerz"
            payment.payment_status = "paid"
            if not payment.transaction_id:
                payment.transaction_id = tran_id
            payment.save()

    # Process Admission Fee Payments
    if invoice.invoice_type == "admission_fee" or "admission" in invoice.description.lower():
        payment_month = invoice.created_at.month
        payment, _ = Payment.objects.get_or_create(
            academic_year=enrollment.academic_year,
            student=student,
            month=payment_month
        )

        session_total = 0
        for item in invoice.admission_fee_items.all():
            afp, created = AdmissionFeePayment.objects.get_or_create(
                payment=payment,
                admission_fee_item=item,
                defaults={
                    'amount_paid': item.amount,
                    'payment_status': 'paid'
                }
            )
            if not created:
                afp.amount_paid = item.amount
                afp.payment_status = 'paid'
                afp.save()

            session_total += item.amount

        total_paid = AdmissionFeePayment.objects.filter(
            payment__student=student,
            payment__academic_year=enrollment.academic_year
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        total_due = AdmissionFee.objects.filter(
            admission_fee_policy=enrollment.feestructure.admissionfee_policy
        ).aggregate(total=Sum('amount'))['total'] or 0

        if total_paid >= total_due:
            payment.admission_fee_payment_status = 'paid'
        elif total_paid > 0:
            payment.admission_fee_payment_status = 'partial-paid'
        else:
            payment.admission_fee_payment_status = 'due'

        payment.admission_fee_paid = total_paid
        payment.payment_method = "sslcommerz"
        payment.payment_status = "paid"
        if not payment.transaction_id:
            payment.transaction_id = tran_id
        payment.save()

    # Mark invoice as paid
    invoice.is_paid = True
    invoice.save()

    return redirect('payments:post_payment_redirect', invoice_id=invoice.id)




def post_payment_redirect(request, invoice_id):
    invoice = get_object_or_404(PaymentInvoice, id=invoice_id)
    student = invoice.student

    if invoice.invoice_type == 'consultation':
        return render(request, 'payment_gateway/thank_you_consultation.html', {'student': student})
    elif invoice.invoice_type == 'labtest':
        return render(request, 'payments/thank_you_lab.html', {'invoice': invoice})
    return render(request, 'payments/thank_you_generic.html', {'invoice': invoice})



@csrf_exempt
def payment_fail(request):
    return HttpResponse("Payment failed!")

@csrf_exempt
def payment_cancel(request):
    return HttpResponse("Payment cancelled by user.")





