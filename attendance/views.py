from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib import messages
import json
from django.http import JsonResponse
from datetime import datetime

from django.db.models import Q
from students.models import Student
from teachers.models import Teacher

from.models import Attendance,AttendanceLog,AttendancePolicy
from.forms import AttendanceForm,AttendanceLogForm,AttendancePolicyForm,AttendanceFilterForm,Weekday
from .forms import WeekdayForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

from payment_gatway.utils import send_sms
from messaging.utils import create_notification


@login_required
def manage_weekday(request, id=None):  
    instance = get_object_or_404(Weekday, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = WeekdayForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('attendance:create_weekday')  
    else:
        print(form.errors)

    datas = Weekday.objects.all().order_by('name')
    paginator = Paginator(datas, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = WeekdayForm(instance=instance)
    return render(request, 'attendance/manage_weekday.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_weekday(request, id):
    instance = get_object_or_404(Weekday, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('students:create_weekday') 

    messages.warning(request, "Invalid delete request!")
    return redirect('students:create_weekday') 



@login_required
def manage_attendance_policy(request, id=None):   
    instance = get_object_or_404(AttendancePolicy, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AttendancePolicyForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AttendancePolicyForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False)  
            form_instance.user = request.user
            form_instance.save()  #
            
            if form.cleaned_data.get('weekend'):  
                form_instance.weekend.set(form.cleaned_data['weekend'])  

            form.save_m2m()  

            messages.success(request, message_text)
            return redirect('attendance:create_attendance_policy')  
        else:
            print(form.errors) 

    datas = AttendancePolicy.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) 


    return render(request, 'attendance/manage_attendance_policy.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_attendance_policy(request, id):
    instance = get_object_or_404(AttendancePolicy, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('attendance:create_attendance_policy')    

    messages.warning(request, "Invalid delete request!")
    return redirect('attendance:create_attendance_policy')  






@login_required
def manage_attendance(request, id=None):   
    instance = get_object_or_404(Attendance, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AttendanceForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('attendance:create_attendance')  
        else:
            print(form.errors) 

    datas = Attendance.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

   


    return render(request, 'attendance/manage_attendance.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_attendance(request, id):
    instance = get_object_or_404(Attendance, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('attendance:create_attendance')    

    messages.warning(request, "Invalid delete request!")
    return redirect('attendance:create_attendance')  




@login_required
def manage_attendance_log(request, id=None):   
    instance = get_object_or_404(AttendanceLog, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AttendanceLogForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AttendanceLogForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()  # Save the attendance log

            form_instance.create_attendance()  # <-- THIS UPDATES OR CREATES ATTENDANCE

            messages.success(request, message_text)
            tenant = form_instance.student.user.tenant
            phone_number = form_instance.student.phone_number
            message= f'Dear {form_instance.student} you have checked in successfully today'
            send_sms(tenant, phone_number, message)
            print(f'sms sent successfully')
            create_notification(user=form_instance.student.user, message=message, notification_type='attendance')
            return redirect('attendance:create_attendance_log')  
        else:
            print(form.errors) 

    datas = AttendanceLog.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'attendance/manage_attendance_log.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_attendance_log(request, id):
    instance = get_object_or_404(AttendanceLog, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('attendance:create_attendance_log')    

    messages.warning(request, "Invalid delete request!")
    return redirect('attendance:create_attendance_log')  





#============================================================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from payment_gatway.utils import send_sms
from messaging.models import Message
from accounts.models import CustomUser



class ReceiveAttendanceDataAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            fingerprint_id = data.get("user_id")
            timestamp = parse_datetime(data.get("timestamp"))

            if not fingerprint_id or not timestamp:
                return Response({"status": "error", "message": "user_id and timestamp required"}, status=status.HTTP_400_BAD_REQUEST)

            user = CustomUser.objects.filter(biometric_id = fingerprint_id).first()
            student = Student.objects.filter(user = user).first() if user else None
            teacher = Teacher.objects.filter(user__biometric_id=fingerprint_id).first()

            if not student and not teacher:
                return Response({"status": "error", "message": "No matching user found for fingerprint ID"}, status=status.HTTP_404_NOT_FOUND)

            if student:
                AttendanceLog.objects.create(
                    student=student,
                    date=timestamp.date(),            
                    check_in_time=timestamp.time(),   
                    created_by="Fingerprint Machine"
                )

                time_str = timestamp.strftime('%I:%M %p')
                date_str = timestamp.strftime('%d-%b-%Y')
                message_text = f"{student.first_name} {student.last_name} checked in at {time_str} on {date_str}."

                if student.guardian:
                    Message.objects.create(
                        student=student,
                        guardian=student.guardian,
                        message_content=message_text,
                        message_type="Attendance"
                    )

                create_notification(
                    user=student.user,
                    student=student,
                    notification_type='attendance',
                    message=message_text
                )
            elif teacher:
                AttendanceLog.objects.create(
                    teacher=teacher,
                    date=timestamp.date(),            
                    check_in_time=timestamp.time(),                       
                    created_by="Fingerprint Machine"
                )

            return Response({"status": "success", "message": "Attendance saved"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#====================================================================================================================




def attendance_report(request):
    form = AttendanceFilterForm(request.GET or None) 
    class_name = None
    section = None
    subject = None
    shift = None
    version = None
    class_gender = None
    academic_year=None
    students = Student.objects.none()
    attendances = Attendance.objects.none()
   
    if request.method == 'GET' and form.is_valid():
        # Get cleaned data from form
        date = form.cleaned_data.get("date")
        class_name = form.cleaned_data.get("class_name")
        section = form.cleaned_data.get("section")    
        academic_year = form.cleaned_data.get("academic_year")   
        subject = form.cleaned_data.get("subject")  
        shift = form.cleaned_data.get("shift")    
        class_gender = form.cleaned_data.get("class_gender")   
        language_version = form.cleaned_data.get("version") 
        student = form.cleaned_data.get("student") 
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")
        days = form.cleaned_data.get("days")

        # Initialize all students and attendances
        students = Student.objects.all()
        attendances = Attendance.objects.all()

        if academic_year:
            students = students.filter(enrolled_students__academic_year=academic_year)
            attendances = attendances.filter(student__enrolled_students__academic_year=academic_year)

        if date:
            attendances = attendances.filter(date=date)
        if start_date and end_date:
             attendances = attendances.filter(date__range=[start_date, end_date])
        if days:
            end_date = timezone.now().today()
            start_date = end_date - timedelta(days=days)
            attendances = attendances.filter(date__range=[start_date, end_date])

        if class_name:
            students = students.filter(enrolled_students__student_class=class_name)
            attendances = attendances.filter(student__enrolled_students__student_class=class_name)
        
        if section:
            students = students.filter(enrolled_students__section=section)
            attendances = attendances.filter(student__enrolled_students__section=section)
       
        if shift and shift not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__shift=shift)
            attendances = attendances.filter(student__enrolled_students__student_class__shift=shift)

        if class_gender and class_gender not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__section__class_gender=class_gender)
            attendances = attendances.filter(student__enrolled_students__section__class_gender=class_gender)
        
        if language_version and language_version not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__language_version=language_version)
            attendances = attendances.filter(student__enrolled_students__student_class__language_version=language_version)
        
        if subject:
            students = students.filter(enrolled_students__subjects__in=[subject])
            attendances = attendances.filter(student__enrolled_students__subjects__in=[subject])
        if student:
            students = students.filter(id=student.id)
            attendances = attendances.filter(student__id=student.id)

  

    context = {
        "attendance_records": attendances,
        "students": students,
        'subject': subject,
        'section': section,
        'shift': shift,
        'class_name': class_name,
        'version': version,
        'class_gender': class_gender,       
        'form':form,
        'academic_year':academic_year
    }
    return render(request, "attendance/attendance_report.html", context)




def daily_attendance_summary(request):
    form = AttendanceFilterForm(request.GET or None) 
    students = Student.objects.none()
    attendances = Attendance.objects.none()
    class_name = None
    section = None
    subject = None
    shift = None
    version = None
    class_gender = None
    academic_year=None
   
    if request.method == 'GET' and form.is_valid():
        # Get cleaned data from form
        date = form.cleaned_data.get("date")
        class_name = form.cleaned_data.get("class_name")
        section = form.cleaned_data.get("section")    
        academic_year = form.cleaned_data.get("academic_year")   
        subject = form.cleaned_data.get("subject")  
        shift = form.cleaned_data.get("shift")    
        class_gender = form.cleaned_data.get("class_gender")   
        language_version = form.cleaned_data.get("version") 
        student = form.cleaned_data.get("student") 

        # Initialize all students and attendances
        students = Student.objects.all()
        attendances = Attendance.objects.all()

        if academic_year:
            students = students.filter(enrolled_students__academic_year=academic_year)
            attendances = attendances.filter(student__enrolled_students__academic_year=academic_year)

        if date:
            attendances = attendances.filter(date=date)
        if class_name:
            students = students.filter(enrolled_students__student_class__academic_class__name=class_name)
            attendances = attendances.filter(student__enrolled_students__student_class__academic_class__name=class_name)
        
        if section:
            students = students.filter(enrolled_students__section=section)
            attendances = attendances.filter(student__enrolled_students__section=section)
       
        if shift and shift not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__shift=shift)
            attendances = attendances.filter(student__enrolled_students__student_class__shift=shift)

        if class_gender and class_gender not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__section__class_gender=class_gender)
            attendances = attendances.filter(student__enrolled_students__section__class_gender=class_gender)
        
        if language_version and language_version not in [None, '', 'not-applicable']:
            students = students.filter(enrolled_students__student_class__language_version=language_version)
            attendances = attendances.filter(student__enrolled_students__student_class__language_version=language_version)
        
        if subject:
            students = students.filter(enrolled_students__subjects__in=[subject])
            attendances = attendances.filter(student__enrolled_students__subjects__in=[subject])
        if student:
            students = students.filter(id=student.id)
            attendances = attendances.filter(student__id=student.id)

     # Calculate totals
    total_students = students.count()
    total_present = attendances.filter(status="Present").count() if attendances.exists() else 0
    total_absent = attendances.filter(status="Absent").count() if attendances.exists() else 0
    total_late = attendances.filter(is_late=True).count() if attendances.exists() else 0
    total_early_out = attendances.filter(is_early_out=True).count() if attendances.exists() else 0

    # Prepare the summary data
    attendance_summary_data = {
        'total_students': total_students,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_early_out':total_early_out,
        'class_gender': class_gender,
        'academic_year':academic_year  
    }


    context = {
        'attendance_summary_data': json.dumps(attendance_summary_data),
        'form': form,        
        'total_students': total_students,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,   
        'total_early_out':total_early_out,
        'subject': subject,
        'section': section,
        'shift': shift,
        'class_name': class_name,
        'version': version,
        'class_gender': class_gender,
        'academic_year':academic_year  



    }

    return render(request, 'attendance/daily_attendance_summary.html', context)
