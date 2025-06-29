from django.shortcuts import render, redirect, get_object_or_404
from .models import Student,StudentEnrollment,Guardian
from django.forms import inlineformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from school_management.models import Subject,AcademicClass,Section

from .forms import StudentEnrollmentForm,GuardianForm,StudentForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages



@login_required
def manage_guardian(request, id=None):  
    instance = get_object_or_404(Guardian, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = GuardianForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('students:create_guardian')  
    else:
        print(form.errors)

    datas = Guardian.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = GuardianForm(instance=instance)
    return render(request, 'students/manage_guardian.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_guardian(request, id):
    instance = get_object_or_404(Guardian, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('students:create_guardian')  

    messages.warning(request, "Invalid delete request!")
    return redirect('students:create_guardian') 





@login_required
def manage_student(request, id=None):  
    instance = get_object_or_404(Student, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = StudentForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)       
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('students:create_student')  
    else:
        print(form.errors)

    datas = Student.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = StudentForm(instance=instance)
    return render(request, 'students/manage_student.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_student(request, id):
    instance = get_object_or_404(Student, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('students:create_student')  

    messages.warning(request, "Invalid delete request!")
    return redirect('students:create_student') 




@login_required
def manage_student_enrollment(request, id=None):  
    instance = get_object_or_404(StudentEnrollment, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = StudentEnrollmentForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('students:create_student_enrollment')  
    else:
        print(form.errors)
    students = Student.objects.all()  # Fetch students from DB
    student_classes = AcademicClass.objects.all()  # Fetch classes from DB
    sections = Section.objects.all()  # Fetch sections from DB
    subjects = Subject.objects.all()
    print(subjects)

    datas = StudentEnrollment.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = StudentEnrollmentForm(instance=instance)
    return render(request, 'students/manage_student_enrollment.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj,
        'students':students,
        'student_classes':student_classes,
        'sections':sections,
        'subjects':subjects
    })


@login_required
def delete_student_enrollment(request, id):
    instance = get_object_or_404(StudentEnrollment, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('students:create_student_enrollment')  

    messages.warning(request, "Invalid delete request!")
    return redirect('students:create_student_enrollment') 



def enroll_student(request):
    if request.method == "POST":
        form = StudentEnrollmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("success_page")  # Replace with your success redirect
    else:
        form = StudentEnrollmentForm()

    students = Student.objects.all() 
    sections = Section.objects.all() 
    student_classes = AcademicClass.objects.all()  

    return render(request, "students/student_enrollment.html", {
        "form": form,
        "students": students,
        "sections": sections,
        "student_classes": student_classes
    })


def get_subjects(request):
    class_id = request.GET.get('class_id')
    if class_id:
        subjects = Subject.objects.filter(academic_class_id=class_id).values('id', 'name')
        return JsonResponse(list(subjects), safe=False)
    return JsonResponse([], safe=False)



from.models import Student
from.forms import StudentFilterForm
@login_required
def view_student_vcard(request):
    student_name = None
    student_records = Student.objects.all().order_by('-created_at')

    form=StudentFilterForm(request.GET or None)

    if form.is_valid():
        student_id = form.cleaned_data['student_id']
        if student_id:
            student_records=student_records.filter(student_id=student_id)

    paginator = Paginator(student_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    form=StudentFilterForm()
    return render(request, 'students/view_student_vcard.html', 
    {
        'student_records': student_records,
        'form':form,
        'page_obj':page_obj
    })

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Student

def get_student_details(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    
    # Constructing the response
    data = {
        "name": student.name,
        "student_id": student.student_id,
        "class": student.enrolled_students.first().student_class.name if student.enrolled_students.exists() else "N/A",
        "section": student.enrolled_students.first().section.name if student.enrolled_students.exists() else "N/A",
        "shift": student.enrolled_students.first().student_class.shift if student.enrolled_students.exists() else "N/A",
        "gender": student.enrolled_students.first().section.class_gender if student.enrolled_students.exists() else "N/A",
        "language_version": student.enrolled_students.first().student_class.language_version if student.enrolled_students.exists() else "N/A",
        'phone_number':student.phone_number if student.phone_number else 'N/A',
        'Email':student.email if student.email else 'N/A',
        'address':student.address if student.address else 'N/A',
        'guardian':student.guardian.name if student.guardian.name else 'N/A',
        'guardian_phone':student.guardian.phone_number if student.guardian.phone_number else 'N/A',
        'guardian_email':student.guardian.email if student.guardian.email else 'N/A',
        'Relationship':student.guardian.relationship if student.guardian.relationship else 'N/A'
    }
    
    return JsonResponse(data)








from openpyxl import Workbook
from io import BytesIO
from django.http import HttpResponse

from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4,letter
from reportlab.pdfgen import canvas
from django.utils import timezone
import os
import base64
from django.conf import settings
from.models import Student
from reportlab.lib.pagesizes import A5
from core.models import Employee
from results.models import Result, ExamType
from reportlab.lib.pagesizes import A5, landscape



def generate_admit_card_pdf(student, exam_type):
    buffer = BytesIO()
    CUSTOM_ADMIT_SIZE = (A5[0] /1.1, A5[1] / 1.3)
    # pdf_canvas = canvas.Canvas(buffer, pagesize=A5)
    pdf_canvas = canvas.Canvas(buffer, pagesize=CUSTOM_ADMIT_SIZE)
    
    # width, height = A5
    width, height = CUSTOM_ADMIT_SIZE
    margin = 40
    y = height - margin

    # === School Info ===
    school = student.enrolled_students.first().academic_class.faculty.school
    class_info = student.enrolled_students.first().student_class
    section_info = student.enrolled_students.first().section
    academic_year = student.enrolled_students.first().academic_year
    exam = exam_type

    # Draw Border
    pdf_canvas.setStrokeColorRGB(0.2, 0.5, 0.3)
    pdf_canvas.setLineWidth(1)
    pdf_canvas.rect(margin / 2, margin / 2, width - margin, height - margin)

    # Logo
    if school.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, school.logo.name)
        pdf_canvas.drawImage(logo_path, margin, y - 50, width=50, height=50)

    # School Name
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawCentredString(width / 2, y, school.name)

    # School Address & Website
    pdf_canvas.setFont("Helvetica", 10)
    y -= 20
    pdf_canvas.drawCentredString(width / 2, y, school.address)
    y -= 15
    pdf_canvas.drawCentredString(width / 2, y, school.website)

    # Admit Card Title
    y -= 30
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.setFillColorRGB(0.1, 0.2, 0.5)
    pdf_canvas.drawCentredString(width / 2, y, "STUDENT ADMIT CARD")
    pdf_canvas.setFillColorRGB(0, 0, 0)

    # === Student Info Section ===
    y -= 40
    pdf_canvas.setFont("Helvetica", 10)
    info_lines = [
        f"Student ID: {student.student_id}",
        f"Name: {student.name}",
        f"Class: {class_info.academic_class.name}",
        f"Version: {class_info.language_version}",
        f"Shift: {class_info.shift}",
        f"Section: {section_info.name}",
        f"Class Gender: {section_info.class_gender}",
        f"Academic Year: {academic_year}"
    ]
    for line in info_lines:
        pdf_canvas.drawString(margin + 10, y, line)
        y -= 15

    # === Exam Info ===
    y -= 10
    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.drawString(margin + 10, y, "Exam Information:")
    y -= 15
    pdf_canvas.setFont("Helvetica", 10)
    exam_lines = [
        f"Exam Name: {exam.exam.name}",
        f"Exam Date: {exam.exam_date.strftime('%d %B %Y') if exam.exam_date else 'TBA'}",
    ]
    for line in exam_lines:
        pdf_canvas.drawString(margin + 30, y, line)
        y -= 15

    # === Authorization Section ===
    y -= 30
    cfo = Employee.objects.filter(position__name='CFO').first()
    pdf_canvas.setFont("Helvetica", 9)
    pdf_canvas.drawString(margin + 10, y, "Authorized Signature: ___________________________")
    y -= 15
    if cfo:
        pdf_canvas.drawString(margin + 30, y, f"Name: {cfo.name}")
        y -= 15
        pdf_canvas.drawString(margin + 30, y, f"Designation: {cfo.position}")
    else:
        pdf_canvas.drawString(margin + 30, y, "Name: _____________")
        y -= 15
        pdf_canvas.drawString(margin + 30, y, "Designation: ____________")

    # === Footer ===
    pdf_canvas.setFont("Helvetica-Oblique", 7)
    pdf_canvas.setFillColorRGB(0.3, 0.5, 0.3)
    pdf_canvas.drawCentredString(width / 2, 25, "Digitally authorized. No signature required.")

    pdf_canvas.save()
    buffer.seek(0)
    return buffer





@login_required
def preview_admit_card(request, student_id, exam_id):
    student = get_object_or_404(Student, id=student_id)
    exam_type = get_object_or_404(ExamType, id=exam_id)
    exam_date = exam_type.exam_date

    cleared_fees, total_due = has_cleared_required_fees(student, exam_date)

#    if not cleared_fees:
#        return render(request, "students/admit_card_blocked.html", {
#            "message": "You cannot download the admit card until all dues are cleared up to the exam date.",
#            "total_due": total_due
#        })

    pdf_buffer = generate_admit_card_pdf(student, exam_type)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')

    return render(request, "students/preview_admit_card.html", {
        "student": student,
        "exam_type": exam_type,
        "pdf_preview": pdf_base64,
    })



from decimal import Decimal
from django.db.models import Sum, F

def has_cleared_required_fees(student, exam_date):
    exam_year = exam_date.year
    payments_due = student.student_payments.filter(
        academic_year=exam_year,
        due_date__lte=exam_date
    )

    total_due = Decimal('0.00')
    if not payments_due.exists():        
        return False, total_due

    unpaid = payments_due.filter(payment_status='due')
    partial = payments_due.filter(payment_status='partial-paid')

    for payment in unpaid.union(partial):
        total_due += payment.remaining_due or 0

    admission_fee_due = student.student_payments.filter(
        payment_status='due',
        due_date__lte=exam_date
        ).exclude(admission_fee_paid=F('admission_fee_paid'))
    
    for fee in admission_fee_due:
        total_due += fee.remaining_due or 0

    if unpaid.exists() or partial.exists() or admission_fee_due.exists():
        return False, total_due
    return True, Decimal('0.00')




@login_required
def student_exam_schedule(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    exam_types = ExamType.objects.filter(
        exam_results__student=student
    ).distinct().order_by('exam_date')

    exam_status = []
    for exam in exam_types:
        exam_status.append({
            "exam": exam,
            "fees_clear": has_cleared_required_fees(student, exam.exam_date)
        })

    return render(request, "students/student_exam_list.html", {
        "student": student,
        "exam_types": exam_types,
        "exam_status": exam_status,
    })




from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from school_management.models import Schedule, AcademicClass, Section
from datetime import datetime,timedelta
from .models import Student
from django.core.exceptions import PermissionDenied





def student_weekly_schedule_with_id(request,student_id):
    student = get_object_or_404(Student,id=student_id)
  
    context = {
        'student': None,
        'schedule_by_day': None,
        'filtered_schedule': None,
        'day_filter': request.GET.get('day'),
    }
   
    if not student:
        return render(request, 'students/student_specific_class_schedule.html', context)

    enrollment = student.enrolled_students.first()
    if not enrollment:
        context['error'] = 'No enrollment found for this student.'
        return render(request, 'students/student_specific_class_schedule.html', context)

    academic_class = enrollment.academic_class
    section = enrollment.section
    gender = section.class_gender
    academic_year = enrollment.academic_year
    shift = enrollment.student_class.shift
    version = enrollment.student_class.language_version
    day_filter = context['day_filter']

    base_queryset = Schedule.objects.filter(
        subject_assignment__class_assignment__academic_class=academic_class,
        subject_assignment__section=section,
        subject_assignment__academic_year=academic_year,
        subject_assignment__class_assignment__language_version=version,
        shift=shift,
        gender=gender,
    )

    if day_filter:
        base_queryset = base_queryset.filter(day_of_week__iexact=day_filter)

    schedules = base_queryset.select_related(
        'subject_assignment__subject',
        'subject_assignment__subject_teacher',
        'class_room'
    ).order_by('day_of_week', 'start_time')

    schedule_by_day = defaultdict(list)
    if not day_filter:
        for s in schedules:
            schedule_by_day[s.day_of_week].append(s)

    # Add context and render
    context.update({
        'student': student,
        'academic_class': academic_class,
        'section': section,
        'academic_year': academic_year,
        'shift': shift,
        'version': version,
        'gender': gender,
        'filtered_schedule': schedules if day_filter else None,
        'schedule_by_day': dict(schedule_by_day) if not day_filter else None,
    })

    return render(request, 'students/student_specific_class_schedule.html', context)




def student_weekly_schedule(request):
    student = None
    student_id = request.GET.get("student_id")
    context = {
        'student': None,
        'schedule_by_day': None,
        'filtered_schedule': None,
        'day_filter': request.GET.get('day'),
    }

    if student_id:
        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            messages.warning(request, 'Invalid student ID provided.')
            return redirect('core:dashboard')
    elif hasattr(request.user, 'student'):
        student = request.user.student
    if not student:
        return render(request, 'students/student_specific_class_schedule.html', context)

    enrollment = student.enrolled_students.first()
    if not enrollment:
        context['error'] = 'No enrollment found for this student.'
        return render(request, 'students/student_specific_class_schedule.html', context)

    academic_class = enrollment.academic_class
    section = enrollment.section
    gender = section.class_gender
    academic_year = enrollment.academic_year
    shift = enrollment.student_class.shift
    version = enrollment.student_class.language_version
    day_filter = context['day_filter']

    base_queryset = Schedule.objects.filter(
        subject_assignment__class_assignment__academic_class=academic_class,
        subject_assignment__section=section,
        subject_assignment__academic_year=academic_year,
        subject_assignment__class_assignment__language_version=version,
        shift=shift,
        gender=gender,
    )

    if day_filter:
        base_queryset = base_queryset.filter(day_of_week__iexact=day_filter)

    schedules = base_queryset.select_related(
        'subject_assignment__subject',
        'subject_assignment__subject_teacher',
        'class_room'
    ).order_by('day_of_week', 'start_time')

    schedule_by_day = defaultdict(list)
    if not day_filter:
        for s in schedules:
            schedule_by_day[s.day_of_week].append(s)

    # Add context and render
    context.update({
        'student': student,
        'academic_class': academic_class,
        'section': section,
        'academic_year': academic_year,
        'shift': shift,
        'version': version,
        'gender': gender,
        'filtered_schedule': schedules if day_filter else None,
        'schedule_by_day': dict(schedule_by_day) if not day_filter else None,
    })

    return render(request, 'students/student_specific_class_schedule.html', context)









def view_student_weekly_schedule(request):
    # Get filter params from GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    number_of_days = request.GET.get('days')
    specific_date = request.GET.get('date')
    section_id = request.GET.get('section')
    class_id = request.GET.get('class')
    shift = request.GET.get('shift')
    gender = request.GET.get('gender')
    academic_year = request.GET.get('academic_year')  # Optional, useful if user selects year

    base_queryset = Schedule.objects.all()

    # Apply filters dynamically
    if class_id:
        base_queryset = base_queryset.filter(subject_assignment__class_assignment__academic_class_id=class_id)

    if section_id:
        base_queryset = base_queryset.filter(subject_assignment__section_id=section_id)

    if academic_year:
        base_queryset = base_queryset.filter(subject_assignment__academic_year=academic_year)

    if shift:
        base_queryset = base_queryset.filter(shift=shift)

    if gender:
        base_queryset = base_queryset.filter(gender=gender)

    # Apply date-based filtering
    if specific_date:
        base_queryset = base_queryset.filter(date=specific_date)

    if start_date and end_date:
        base_queryset = base_queryset.filter(date__range=[start_date, end_date])
    elif number_of_days:
        today = datetime.today()
        days = [(today + timedelta(days=i)).strftime('%A') for i in range(int(number_of_days))]
        base_queryset = base_queryset.filter(day_of_week__in=days)

    # Prefetch for performance
    schedules = base_queryset.select_related(
        'subject_assignment__subject',
        'subject_assignment__subject_teacher',
        'class_room'
    ).order_by('day_of_week', 'start_time')

    # Group schedule by weekday
    schedule_by_day = defaultdict(list)
    for s in schedules:
        schedule_by_day[s.day_of_week].append(s)

    return render(request, 'students/student_class_schedule.html', {
        'schedule_by_day': dict(schedule_by_day),
        'filters_applied': {
            'class': class_id,
            'section': section_id,
            'academic_year': academic_year,
            'shift': shift,
            'gender': gender,
            'start_date': start_date,
            'end_date': end_date,
            'specific_date': specific_date,
            'days': number_of_days,
        },
        'classes': AcademicClass.objects.all(),
        'sections': Section.objects.all(),
    })


def get_days_between(start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    delta = (end_date - start_date).days
    return [(start_date + timedelta(days=i)).strftime('%A') for i in range(delta + 1)]
