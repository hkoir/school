

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings

from collections import defaultdict,Counter
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Max, Count,Sum,F,Count,Q,OuterRef, Subquery
from collections import defaultdict

import os
import json
import base64
import requests
import uuid
from decimal import Decimal
from datetime import date
from datetime import datetime,timedelta

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse

from reportlab.lib.pagesizes import landscape, A4,letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageTemplate
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from payments.utils import get_due_till_today, apply_payment_to_oldest_months, create_payment_invoice,apply_one_time_payment
from payment_gatway.models import PaymentSystem,TenantPaymentConfig
from payments.forms import FeePaymentForm
from payments.models import (
    Payment,PaymentInvoice,AdmissionFeePayment,AdmissionFee,TuitionFeePayment,
    Payment
    )
from messaging.forms import ReplyMessageForm,ConversationFilterForm,CommunicationMessageForm
from messaging.models import CommunicationMessage,Conversation,MessageReadStatus
from accounts.models import CustomUser
from school_management.models import Schedule, AcademicClass, Section,Subject,Schedule
from results.forms import StudentTranscriptFilterForm
from results.models import Exam,ExamType,Result,StudentFinalResult,Grade
from students.models import StudentEnrollment
from.forms import StudentAttendanceFilterForm,AcademicYearFilterForm,ExamResultForm
from attendance.forms import AttendanceFilterForm
from attendance.models import Attendance
from core.models import Notice,Employee
from core.forms import NoticeForm
from students.models import Student





def student_landing_page(request):
    student = Student.objects.filter(user=request.user).first()  
    student_results = Result.objects.filter(
        student=student,
        academic_year=timezone.now().year
    )
    exam_ids = student_results.values_list('exam_type__exam', flat=True).distinct()

    exam_overall = {}
    for exam_id in exam_ids:
        exam = Exam.objects.get(id=exam_id)
        data = student.get_exam_overall(exam)
        if data:
            exam_overall[exam.name] = data


    student_final_result = (
        StudentFinalResult.objects
        .filter(student=student, academic_year=timezone.now().year)
        .order_by('-created_at')
        .first()
    )

    upcoming_exams= Exam.objects.filter(is_exam_over = False)
    dues = get_due_till_today(student)
    has_due = any(d['net_due'] > 0 for d in dues.values())

    return render(request, 'student_portal/student_landing_page.html', {
        'student': student,
        'student_last_result': student_final_result,
        'student_results': student_results,
        'exam_overall':exam_overall,
        'upcoming_exams':upcoming_exams,
        'has_due':has_due
    
    })

@login_required
def view_student_vcard(request):   
    student_records=Student.objects.filter(user=request.user).first()  
    return render(request, 'student_portal/view_student_vcard.html', {'student_records': student_records,'student':student_records})
    

@login_required
def view_notices(request):
    notices = Notice.objects.all().order_by('-created_at')
    form = NoticeForm()
    return render(request, 'student_portal/view_notices.html', {'notices': notices, 'form': form})





def attendance_report(request):  
    form = StudentAttendanceFilterForm(request.GET or {'days': 7})    
    attendances = Attendance.objects.none()  
    student = None   

    if request.user.is_authenticated and request.user.role == 'student':
        student = Student.objects.filter(user=request.user).first()

    if student:
        attendances = Attendance.objects.filter(student=student).order_by('-date')

        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")
            days = form.cleaned_data.get("days")        
            academic_year = form.cleaned_data.get("academic_year")        

            if start_date and end_date:
                attendances = attendances.filter(date__range=(start_date, end_date))
            elif days:
                end_date = datetime.today().date()
                start_date = end_date - timedelta(days=days)
                attendances = attendances.filter(date__range=(start_date, end_date))     

            if academic_year:            
                attendances = attendances.filter(student__enrolled_students__academic_year=academic_year)

    
    form = StudentAttendanceFilterForm()

    paginator = Paginator(attendances, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "attendance_records": page_obj,
        "form": form, 
        "page_obj": page_obj,
    }

    return render(request, "student_portal/attendance_report.html", context)




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




def exam_schedule_view(request):
    exam_id = request.GET.get('exam')
    class_id = request.GET.get('class')
    exam=None

    exams = Exam.objects.all().order_by('-academic_year')
    classes = AcademicClass.objects.all()

    exam_schedule = []
    if exam_id and class_id:
        exam = get_object_or_404(Exam, id=exam_id)
        academic_class = get_object_or_404(AcademicClass, id=class_id)       

        exam_schedule = exam.exam_types.filter(
            academic_class=academic_class
        ).select_related('subject', 'room').order_by('exam_date', 'start_time')       

    context = {
        'exams': exams,
        'classes': classes,
        'exam_schedule': exam_schedule,
        'selected_exam': exam_id,
        'selected_class': class_id,
        'exam':exam
    }

    return render(request, 'student_portal/exam_schedule.html', context)



def exam_list(request):
    exams = Exam.objects.all()
    student = Student.objects.filter(user=request.user).first
    return render(request,'student_portal/exam_list.html',{'exams':exams,'student':student})
 

def generate_admit_card_pdf(student, exam_type):
    buffer = BytesIO()
    CUSTOM_ADMIT_SIZE = (A5[0] / 1.1, A5[1] / 1.3)
    pdf_canvas = canvas.Canvas(buffer, pagesize=CUSTOM_ADMIT_SIZE)
    
    width, height = CUSTOM_ADMIT_SIZE
    margin = 30
    current_y = height - margin

    # === School Info ===
    school = student.enrolled_students.first().academic_class.faculty.school
    class_info = student.enrolled_students.first().academic_class
    section_info = student.enrolled_students.first().section
    academic_year = student.enrolled_students.first().academic_year
    exam = exam_type

    # Draw Border
    pdf_canvas.setStrokeColorRGB(0.2, 0.5, 0.3)
    pdf_canvas.setLineWidth(1)
    pdf_canvas.rect(margin / 2, margin / 2, width - margin, height - margin)

    # --- Logo ---
    logo_height = 40
    logo_width = 40
    logo_spacing = 10  # space below logo
    if school.logo:       
        logo_path = os.path.join(settings.MEDIA_ROOT, school.logo.name)
        pdf_canvas.drawImage( logo_path, width/2 - logo_width/2, current_y - logo_height, width=logo_width, height=logo_height)
      
    current_y -= (logo_height + logo_spacing)

    # --- School Name ---
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawCentredString(width / 2, current_y, school.name)

    # --- School Address & Website ---
    current_y -= 20
    pdf_canvas.setFont("Helvetica", 10)
    pdf_canvas.drawCentredString(width / 2, current_y, school.address)
    current_y -= 15
    pdf_canvas.drawCentredString(width / 2, current_y, school.website)

    # --- Admit Card Title ---
    current_y -= 30
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.setFillColorRGB(0.1, 0.2, 0.5)
    pdf_canvas.drawCentredString(width / 2, current_y, "STUDENT ADMIT CARD")
    pdf_canvas.setFillColorRGB(0, 0, 0)

    # === Student Info Section ===
    current_y -= 40
    pdf_canvas.setFont("Helvetica", 10)
    info_lines = [
        f"Student ID: {student.student_id}",
        f"Name: {student.name}",
        f"Class: {class_info.name}",
        f"Version: {student.enrolled_students.first().language}",
        f"Shift: {student.enrolled_students.first().shift.name}",
        f"Section: {student.enrolled_students.first().section.name}",
        f"Class Gender: {student.enrolled_students.first().gender.name}",
        f"Academic Year: {academic_year}"
    ]
    for line in info_lines:
        pdf_canvas.drawString(margin + 10, current_y, line)
        current_y -= 15

    # === Exam Info Section ===
    current_y -= 10
    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.drawString(margin + 10, current_y, "Exam Information:")
    current_y -= 15
    pdf_canvas.setFont("Helvetica", 10)
    exam_lines = [
        f"Exam Name: {exam.name}",
        f"Exam Date: {exam.exam_start_date.strftime('%d %B %Y') if exam.exam_start_date else 'TBA'}",
    ]
    for line in exam_lines:
        pdf_canvas.drawString(margin + 30, current_y, line)
        current_y -= 15

    # === Authorization Section ===
    current_y -= 30
    cfo = Employee.objects.filter(position__name='CFO').first()
    pdf_canvas.setFont("Helvetica", 9)
    pdf_canvas.drawString(margin + 10, current_y, "Authorized Signature: ___________________________")
    current_y -= 15
    if cfo:
        pdf_canvas.drawString(margin + 30, current_y, f"Name: {cfo.name}")
        current_y -= 15
        pdf_canvas.drawString(margin + 30, current_y, f"Designation: {cfo.position}")
    else:
        pdf_canvas.drawString(margin + 30, current_y, "Name: _____________")
        current_y -= 15
        pdf_canvas.drawString(margin + 30, current_y, "Designation: ____________")

    # === Footer ===
    pdf_canvas.setFont("Helvetica-Oblique", 7)
    pdf_canvas.setFillColorRGB(0.3, 0.5, 0.3)
    pdf_canvas.drawCentredString(width / 2, 25, "Digitally authorized. No signature required.")

    pdf_canvas.save()
    buffer.seek(0)
    return buffer


@login_required
def preview_admit_card(request, exam_id):   
    student=Student.objects.filter(user=request.user).first()
    exam_type = get_object_or_404(Exam, id=exam_id)
    exam_date = exam_type.exam_start_date

    cleared_fees, total_due = has_cleared_required_fees(student, exam_date)

    # if not cleared_fees:
    #     return render(request, "student_portal/admit_card_blocked.html", {
    #         "message": "You cannot download the admit card until all dues are cleared up to the exam date.",
    #         "total_due": total_due
    #     })

    pdf_buffer = generate_admit_card_pdf(student, exam_type)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')

    return render(request, "student_portal/preview_admit_card.html", {
        "student": student,
        "exam_type": exam_type,
        "pdf_preview": pdf_base64,
    })



def individual_exam_result(request):
    form = ExamResultForm(request.GET or None)
    exam_results_grouped = defaultdict(list)
    student = None
    academic_year = None
    exam_id = None
    exam =None

    if form.is_valid():
        academic_year = form.cleaned_data['academic_year']
        exam = form.cleaned_data.get('exam')
        exam_id = exam.id if exam else None

        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.warning(request, 'No record found for this student')
            return redirect('student_portal:student_landing_page')

        # Filter results for this student and academic year
        query = Result.objects.filter(
            student=student,
            academic_year=academic_year
        ).select_related('exam_type', 'exam_type__subject', 'exam_type__exam')

        if exam_id:
            query = query.filter(exam_type__exam_id=exam_id)

        # Prepare aggregation data
        max_marks = Result.objects.filter(academic_year=academic_year).values('exam_type__exam')\
            .annotate(max_marks=Max('obtained_marks'))
        total_students = Result.objects.filter(academic_year=academic_year).values('exam_type__exam')\
            .annotate(total=Count('student', distinct=True))

        max_marks_dict = {entry['exam_type__exam']: entry['max_marks'] for entry in max_marks}
        total_students_dict = {entry['exam_type__exam']: entry['total'] for entry in total_students}

        # Group results by Exam
        for result in query:
            exam_label = result.exam_type.exam.name  # e.g., "Class Test 1"
            result.max_obtained_marks = max_marks_dict.get(result.exam_type.exam.id, 0)
            result.total_student = total_students_dict.get(result.exam_type.exam.id, 0)
            result.percentage = (result.obtained_marks / result.exam_marks) * 100 if result.exam_marks else 0
            exam_results_grouped[exam_label].append(result)

    return render(request, 'student_portal/individual_exam_result.html', {
        'form': form,
        'exam_results_grouped': dict(exam_results_grouped),
        'student': student,
        'academic_year': academic_year,
        'exam_type_id': exam_id,  # For your template logic
        'selected_exam':exam
    })


def aggregated_final_result(request):  
    student = None  
    student_with_golden_gpa_5 = False
    total_students = Student.objects.all().count()

    if request.user.is_authenticated and request.user.role == 'student':
        student = Student.objects.filter(user=request.user).first()
      
    if not student:
        return render(request, 'student_portal/aggregated_final_result.html', {
            'message': 'Student not found.',
            'student': student
        })

    academic_year = request.POST.get('academic_year')
    if not academic_year:
        return render(request, 'student_portal/aggregated_final_result.html', {
            'message': 'Academic Year is missing.',
            'student': student
        })   

    final_results = StudentFinalResult.objects.filter(
        student=student, 
        academic_year=academic_year
    ).select_related('faculty', 'subject', 'academic_class', 'section', 'final_grade')

    if not final_results.exists():
        return render(request, 'student_portal/aggregated_final_result.html', {
            'message': 'No results found for the given student and academic year.',
            'student': student
        })     

    total_obtained_marks = 0
    total_assigned_marks = 0
    max_obtained_marks = 0
    subject_max_marks = {}  
    all_gpa_5 = True

    for result in final_results:
        total_obtained_marks += result.total_obtained_marks
        total_assigned_marks += result.total_assigned_marks
        max_obtained_marks = max(max_obtained_marks, result.total_obtained_marks)
        subject_max_marks[result.subject.id] = max(
            subject_max_marks.get(result.subject.id, 0), 
            result.total_obtained_marks
        )
        if result.final_grade.grade_point != 5.0:
            all_gpa_5 = False

    student_with_golden_gpa_5 = all_gpa_5

    overall_percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
    final_grade = Grade.objects.filter(min_marks__lte=overall_percentage, max_marks__gte=overall_percentage).first()
    gpa = final_grade.grade_point if final_grade else 0

    subject_student_count_query = StudentFinalResult.objects.filter(
        academic_year=academic_year
    ).values('subject').annotate(student_count=Count('student'))

    subject_student_count = {
        entry['subject']: entry['student_count'] 
        for entry in subject_student_count_query
    }

    # Annotate each result
    for result in final_results:
        result.highest_marks = subject_max_marks.get(result.subject.id, 0)
        result.total_students = subject_student_count.get(result.subject.id, 0)

    return render(request, 'student_portal/aggregated_final_result.html', {
        'student': student,
        'academic_year': academic_year,
        'final_results': final_results,
        'total_obtained_marks': total_obtained_marks,
        'total_assigned_marks': total_assigned_marks,
        'highest_marks': max_obtained_marks,
        'overall_percentage': overall_percentage,       
        'gpa': gpa,
        'student_with_golden_gpa_5': student_with_golden_gpa_5,
        'total_students':total_students
    })


def student_transcripts(request):
    student_results = []
    final_result = None
    final_results = None
    student_with_golden_gpa_5 = False
    total_assigned_marks = 0
    total_obtained_marks = 0
    overall_percentage=0
    average_gpa=0
    student =None
    form = StudentTranscriptFilterForm(request.GET or None)

   
    student = Student.objects.filter(user=request.user).first()       
    if not student:
        messages.warning(request,'you are not allowed to view this result')
        return redirect('student_portal:view_notices')
    
    student_results = Result.objects.filter(student=student).select_related('exam_type')
    final_result = StudentFinalResult.objects.filter(student=student).first()


    highest_marks_subquery = StudentFinalResult.objects.filter(
        academic_year=OuterRef('academic_year'),
        subject=OuterRef('subject')
    ).order_by().values('subject').annotate(
        highest_marks=Max('total_obtained_marks')
    ).values('highest_marks')


    final_results = StudentFinalResult.objects.filter(
        student=student
    ).select_related('faculty', 'academic_class', 'subject', 'section', 'final_grade').annotate(
        highest_marks=Subquery(highest_marks_subquery)
    )

    
    total_obtained_marks = sum(result.total_obtained_marks for result in final_results)
    total_assigned_marks = sum(result.total_assigned_marks for result in final_results)
    overall_percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
    final_grade = Grade.objects.filter(min_marks__lte=overall_percentage, max_marks__gte=overall_percentage).first()
    average_gpa = final_grade.grade_point if final_grade else 0

    
    
    all_5_0 = True
    for result in final_results:
        if result.final_grade.grade_point != 5.0:
            all_5_0 = False
            break

    student_with_golden_gpa_5 = all_5_0            

    grouped_results = defaultdict(list)    
    for result in student_results:
        exam_type_name = result.exam_type.exam.name if result.exam_type else "Unknown Exam"
        highest_marks = Result.objects.filter(
        exam_type=result.exam_type
        ).aggregate(Max('obtained_marks'))['obtained_marks__max'] or 0
        result.highest_marks = highest_marks
        grouped_results[exam_type_name].append(result)            
               

    context = {
        'form': form,
        'grouped_results': dict(grouped_results), 
        'final_results': final_results,
        'final_result': final_result,
        'student':student,        
        'student_with_golden_gpa_5': student_with_golden_gpa_5,
        'average_gpa':average_gpa,
        'overall_percentage':overall_percentage,
        "total_obtained_marks":total_obtained_marks,
        'total_assigned_marks': total_assigned_marks

    }

    return render(request, 'student_portal/student_transcripts.html', context)



def download_final_result(request):
    if request.method == 'POST':
        academic_year = request.POST.get('academic_year')
        if not academic_year:
            messages.warning(request, 'Please select an academic year.')
            return redirect('student_portal:aggregated_final_result')
        return generate_pdf(request, academic_year=academic_year)    
   
    return render(request,'student_portal/download_final_result.html')
    
 

def generate_pdf(request,academic_year):
    student_with_golden_gpa_5=False
    student = Student.objects.filter(user=request.user).first()  

    if not student:
        return HttpResponse(f"Student with ID {student.student_id} not found.", status=404)
    if not academic_year:
        messages.warning(request,'Please enter academic year')
        return redirect('student_portal:aggregated_final_result')

    student_results = Result.objects.filter(student__student_id=student.student_id,academic_year=academic_year).select_related('exam_type')
    if not student_results.exists():
        return HttpResponse(f"No results found for student with ID {student.student_id}.", status=404)

    final_results = StudentFinalResult.objects.filter(
        student__student_id=student.student_id,academic_year=academic_year
    ).select_related('faculty', 'subject', 'academic_class', 'section', 'final_grade')

    total_obtained_marks = 0
    total_assigned_marks = 0
    max_obtained_marks = 0
    subject_max_marks = {}  
    all_gpa_5 = True

    for result in final_results:
         if result.final_grade.grade_point != 5.0:
            all_gpa_5 = False

    student_with_golden_gpa_5 = all_gpa_5

    total_grade_points = sum(result.final_grade.grade_point for result in final_results)
    total_subjects = final_results.count()    
    aggregated_gpa = round(total_grade_points / total_subjects, 2) if total_subjects > 0 else 0


    total_assigned_marks = 0
    total_obtained_marks = 0

    total_obtained_marks = sum(result.total_obtained_marks for result in final_results)
    total_assigned_marks = sum(result.total_assigned_marks for result in final_results)
    overall_percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
    final_grade = Grade.objects.filter(min_marks__lte=overall_percentage, max_marks__gte=overall_percentage).first()
    average_gpa = final_grade.grade_point if final_grade else 0
        

    grouped_results = defaultdict(list)
    for result in student_results:
        exam_type_name = result.exam_type.exam.name
        grouped_results[exam_type_name].append(result)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_{student.student_id}_transcript.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        topMargin=20,
        bottomMargin=40,
        leftMargin=40,
        rightMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()
    style = styles['Normal']
 
    def add_page_header(canvas, doc):
        canvas.saveState()
      
        # Add Logo
        if student.enrolled_students.first().academic_class.faculty.school.logo:
            logo_path = os.path.join(settings.MEDIA_ROOT, student.enrolled_students.first().academic_class.faculty.school.logo.name)
            canvas.drawImage(logo_path, 40, 730, width=50, height=50)

        # Add School Name
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(300, 770, student.enrolled_students.first().academic_class.faculty.school.name)

        # Add School Address and Website
        canvas.setFont("Helvetica", 10)
        canvas.drawCentredString(300, 755, student.enrolled_students.first().academic_class.faculty.school.address)
        canvas.drawCentredString(300, 740, student.enrolled_students.first().academic_class.faculty.school.website)

        # Add School Code
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(300, 725, f"School Code: {student.enrolled_students.first().academic_class.faculty.school.code}")

        # Draw a line under the header
        canvas.line(40, 720, 560, 720)
        canvas.restoreState()

    # Set a custom PageTemplate that calls the header function on every page
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='header_template', frames=frame, onPage=add_page_header)
    doc.addPageTemplates([template])

    #Add Student Information only once (not in the header)
    elements.append(Spacer(1, 50))  # Add some space after header
    if student.profile_picture:
        profile_picture_path = os.path.join(settings.MEDIA_ROOT, student.profile_picture.name)
        img = Image(profile_picture_path, width=40, height=40)
        img.hAlign = 'LEFT' 
        elements.append(img)
        elements.append(Spacer(1, 12)) 
    elements.append(Paragraph(f"<b>Student ID:</b> {student.student_id} || <b>Student Name:</b> {student.name}", style))
    elements.append(Paragraph(f"<b>Class:</b> {student.enrolled_students.first().academic_class.name} || <b>Section:</b> {student.enrolled_students.first().section.name}", style))
    elements.append(Paragraph(f"<b>Shift:</b> {student.enrolled_students.first().student_class.shift} || <b>Version:</b> {student.enrolled_students.first().student_class.language_version} || <b>Gender:</b> {student.enrolled_students.first().section.class_gender}", style))
    elements.append(Paragraph(f"<b>Class teacher ID:</b>{student.enrolled_students.first().section.teacher_in_charge.teacher_id}||<b>Name:</b> {student.enrolled_students.first().section.teacher_in_charge}", style))
    elements.append(Spacer(1, 12))

    elements.append(Spacer(1, 12)) 
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.alignment = 1
    style.fontSize = 12
    elements.append(Paragraph(f"<b>Student's Transcripts</b>", style))
    elements.append(Spacer(1, 8)) 
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.alignment = 1
    style.fontSize = 10
    elements.append(Paragraph(f"<b>Academic Year:</b>{student.enrolled_students.first().academic_year}", style))
    elements.append(Spacer(1, 12))

    styles = getSampleStyleSheet()
    style = styles['Normal']



    # Add Exam Results (Page content)
    for exam_type, results in grouped_results.items():
        exam_type_style = ParagraphStyle(
            'exam_type_style',
            parent=style,
            fontSize=12,  
            alignment=1, 
            spaceAfter=6,  
        )
        human_readable_exam_type = exam_type.replace('_', ' ').title()
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f'<b>{human_readable_exam_type}</b>', exam_type_style))
       
       
        table_data = [['Subject', 'Total Marks', 'Obtained Marks', 'Highest Marks']]

        for result in results:
            highest_marks = Result.objects.filter(
                exam_type__subject=result.exam_type.subject, exam_type=result.exam_type
            ).aggregate(Max('obtained_marks'))['obtained_marks__max'] or 0
            table_data.append([result.exam_type.subject.name, result.exam_marks, result.obtained_marks, highest_marks])

        table = Table(table_data, colWidths=[150, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

    # Add Final Result Table
    if final_results.exists():
        elements.append(Spacer(1, 12))
        elements.append(Paragraph('<b>Final Result</b>', styles['Heading2']))
        final_result_data = [['Subject', 'Obtained Marks', 'Total Marks', 'Percentage', 'Final Grade', 'Grade Point']]

        for result in final_results:
            final_result_data.append([
                result.subject.name,
                result.total_obtained_marks,
                result.total_assigned_marks,
                f"{result.percentage}%",
                result.final_grade.name if result.final_grade else "N/A",
                result.final_grade.grade_point if result.final_grade else "N/A",
            ])

        final_result_table = Table(final_result_data, colWidths=[120, 80, 80, 80, 100, 80])
        final_result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(final_result_table)

        # Display GPA or Golden GPA Message
        elements.append(Spacer(1, 12))
        if student_with_golden_gpa_5:
            elements.append(Paragraph(f"Congratulations! Dear &nbsp;{student.name}, You have achieved <b>Golden GPA 5.0</b>", styles['Heading3']))            
        else:
             elements.append(Paragraph(f"GPAAvg: <b>{aggregated_gpa}</b>||AvgGPA:<b>{average_gpa}</b>", styles['Heading3']))
           
           

    # Build the PDF with all elements
    doc.build(elements)
    return response






###################################  Payment Status ########################################


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
        admission_fee_assignment__student=student,
        admission_fee_assignment__admission_fee__admission_fee_policy__academic_year=academic_year
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    return total_paid



def get_student_due_status(student):
    today = date.today()
    current_month = today.month
    current_year = today.year

    enrollment = student.enrolled_students.first()
    
    if not enrollment or not enrollment.feestructure:
        monthly_status = {month: 'not-set' for month in range(1, 13)}
        return {
            'monthly_status': monthly_status,
            'admission_status': 'not-applicable',
            'admission_fee_total': Decimal('0.00'),
            'admission_fee_paid': Decimal('0.00'),
        }

    academic_year = enrollment.academic_year
    monthly_status = {}

    feestructure = enrollment.feestructure
    expected_monthly_fee = feestructure.monthly_tuition_fee

    for month in range(1, 13):       
        paid = TuitionFeePayment.objects.filter(
            student=student,
            academic_year=academic_year,
            month=month
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal(0.00)
      
        if paid >= expected_monthly_fee:
            monthly_status[month] = 'paid'
            continue
        elif paid > 0:
            monthly_status[month] = 'partial-paid'
            continue
      
        if month > current_month +1 :
            monthly_status[month] = 'not-set'
            continue
      
        if month < current_month:
            monthly_status[month] = 'due'
            continue
 
        if month == current_month:
            if today.day < 25:
                monthly_status[month] = 'set'
            else:
                monthly_status[month] = 'due'
            continue

    # ======== ADMISSION FEE STATUS ======== #
    total_fee = get_total_admission_fee(student)
    total_paid = get_total_admission_fee_paid(student)

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
        'admission_fee_total': total_fee,
        'admission_fee_paid': total_paid,
    }




def calculate_tuition_fee_due_and_paid(student):
    today = date.today()
    enrollment = student.enrolled_students.first()

    if not enrollment:
        return 0, 0

    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year
    monthly_fee = fee_structure.monthly_tuition_fee
    due_month = today.month
    if today.day < 25:
        due_month -= 1
    due_month = max(due_month, 0)  
    total_due_amount = monthly_fee * due_month
    total_paid_amount = (
        student.student_tuition_payments
        .filter(academic_year=academic_year)
        .aggregate(total_paid=Sum('amount_paid'))['total_paid']
        or 0
    )

    return total_due_amount, total_paid_amount





def payment_status_view(request):
    form = AcademicYearFilterForm(request.GET or None)
    academic_year = None
    total_due_amount = Decimal('0.00')
    total_paid_amount = Decimal('0.00')
    data = []
    months = [date(1900, i, 1).strftime('%B') for i in range(1, 13)]
    payment_status_data = {}
    student=None
    dues = {}

    if request.method == 'GET' and form.is_valid():
        academic_year = form.cleaned_data.get("academic_year")

    if not academic_year:
        enrollment = StudentEnrollment.objects.filter(student__user=request.user).order_by('-academic_year').first()
        if enrollment:
            academic_year = enrollment.academic_year

    if academic_year:
        student = Student.objects.filter(
            user=request.user,
            enrolled_students__academic_year=academic_year
        ).first()

        if student:
            fee_status = get_student_due_status(student)            
            total_due, total_paid = calculate_tuition_fee_due_and_paid(student)           
            dues = get_due_till_today(student)

            total_due_amount += total_due
            total_paid_amount += total_paid
            print(f'total due=...........{total_due_amount}')

            data.append({
                'student': student,
                'status_by_month': fee_status['monthly_status'],
                'admission_status': fee_status.get('admission_status', 'not-set'),
            })

            payment_status_data = {
                'total_paid': float(total_paid),
                'total_due': float(total_due),
                'total_due_amount': float(total_due_amount),
                'total_paid_amount': float(total_paid_amount),
            }

    context = {
        'form': form,
        'data': data,
        'months': months,
        'payment_status_data': json.dumps(payment_status_data),
        'dues':dues,
        'student':student
    }
    form = AcademicYearFilterForm()
    return render(request, 'student_portal/payment_status.html', context)





def student_dues_overview(request):   
    students = Student.objects.all()
    student = Student.objects.filter(user=request.user).first()
    dues = {}
    total_due = Decimal('0.00')
   
    dues = get_due_till_today(student)
    for fee in dues.values():
        net = fee.get('net_due', 0)
        total_due += Decimal(str(net))
               

    return render(request, 'student_portal/student_dues_overview.html', {
        'students': students[:50],
        'selected_student': student,
        'dues': dues,
        'total_due': total_due,
        
    })




def student_weekly_schedule(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.warning(request, 'Accessible for student only')
        return redirect('core:dashboard')

    enrollment = student.enrolled_students.first()
    if not enrollment:
        return render(request, 'student_portal/student_specific_class_schedule.html', {
            'error': 'No enrollment found for this student.'
        })

    academic_class = enrollment.academic_class
    section = enrollment.section
    gender = enrollment.gender
    academic_year = enrollment.academic_year
    shift = enrollment.shift
    version = enrollment.language

    # Get day from query params
    day_filter = request.GET.get('day')  # e.g., "Monday"

    # Base queryset
    base_queryset = Schedule.objects.filter(
        academic_class=academic_class,
        section=section,
        academic_year=academic_year,
        language=version,
        shift=shift,
        gender=gender,
    )

    if day_filter:
        base_queryset = base_queryset.filter(day_of_week__iexact=day_filter)

    schedules = base_queryset.select_related(
        'subject',
        'subject_teacher',
        'class_room'
    ).order_by('day_of_week', 'start_time')

    # Group by day only if not filtering
    schedule_by_day = defaultdict(list)
    if not day_filter:
        for s in schedules:
            schedule_by_day[s.day_of_week].append(s)

    return render(request, 'student_portal/student_specific_class_schedule.html', {
        'student': student,
        'academic_class': academic_class,
        'section': section,
        'academic_year': academic_year,
        'shift': shift,
        'version': version,
        'gender': gender,
        'day_filter': day_filter,
        'filtered_schedule': schedules if day_filter else None,
        'schedule_by_day': dict(schedule_by_day) if not day_filter else None,
    })




#=================================== Communicationmmessages ====================


def get_or_create_conversation(user1, user2):
    # Order users consistently
    user1, user2 = sorted([user1, user2], key=lambda u: u.id)

    conversation = Conversation.objects.filter(is_group=False, participants=user1)\
                                       .filter(participants=user2)\
                                       .distinct().first()

    if not conversation:
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.set([user1, user2])
        conversation.save()

    return conversation




@login_required
def send_message(request):
    if request.method == 'POST':
        form = CommunicationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            recipients = form.cleaned_data['recipients']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            image = form.cleaned_data.get('image')  # use get to avoid KeyError
            video = form.cleaned_data.get('video')

            for recipient in recipients:
                conversation = get_or_create_conversation(request.user, recipient)
                CommunicationMessage.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    conversation=conversation,
                    image=image if image else None,
                    video=video if video else None
                )
            return redirect('student_portal:inbox')
    else:
        form = CommunicationMessageForm()
    
    return render(request, 'student_portal/conversation_messaging/send_message2.html', {'form': form})



@login_required
def create_group_conversation(request):
    if request.method == "POST":
        name = request.POST.get("name")
        user_ids = request.POST.getlist("participants")
        participants = CustomUser.objects.filter(id__in=user_ids)
        if participants.exists():
            conversation = Conversation.objects.create(name=name, is_group=True)
            conversation.participants.set(participants)
            conversation.participants.add(request.user)
            return redirect("student_portal:group_conversation_detail", pk=conversation.pk)
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, "student_portal/conversation_messaging/create_group_conversation.html", {"users": users})




@login_required
def add_participants(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk, is_group=True)
        if request.user not in conversation.participants.all():
            messages.warning(request, "You are not a participant of this group.")
            return redirect('student_portal:inbox')
    except Conversation.DoesNotExist:
        messages.error(request, "Group conversation not found.")
        return redirect('student_portal:inbox')

    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id__in=conversation.participants.all())
        conversation.participants.add(*users)
        messages.success(request, "Participants added successfully.")
        return redirect('student_portal:inbox', pk=conversation.pk)

    available_users = CustomUser.objects.exclude(id__in=conversation.participants.all())
    return render(request, "student_portal/conversation_messaging/add_participants.html", {
        "conversation": conversation,
        "available_users": available_users
    })


@login_required
def remove_participants(request, pk):
    try:
        conversation = Conversation.objects.get(pk=pk, is_group=True)
        if request.user not in conversation.participants.all():
            messages.warning(request, "You are not a participant of this group.")
            return redirect('student_portal:inbox')
    except Conversation.DoesNotExist:
        messages.error(request, "Group conversation not found.")
        return redirect('student_portal:inbox')

    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        conversation.participants.remove(*users)
        messages.success(request, "Participants removed successfully.")
        return redirect('student_portal:inbox', pk=conversation.pk)

    current_participants = conversation.participants.exclude(id=request.user.id)
    return render(request, "student_portal/conversation_messaging/remove_participants.html", {
        "conversation": conversation,
        "current_participants": current_participants
    })




@login_required
def edit_message(request, message_id):
    try:
        msg = CommunicationMessage.objects.get(id=message_id)
        if msg.sender != request.user:
            messages.warning(request, "You are not allowed to edit this message.")
            return redirect('student_portal:inbox', pk=msg.conversation.id)
    except CommunicationMessage.DoesNotExist:
        messages.error(request, "Message not found.")
        return redirect('student_portal:inbox')  # fallback or change this as needed

    if request.method == 'POST':
        form = ReplyMessageForm(request.POST, request.FILES, instance=msg)
        if form.is_valid():
            form.save()
            messages.success(request, "Message updated successfully.")
            return redirect('student_portal:inbox', pk=msg.conversation.id)
    else:
        form = ReplyMessageForm(instance=msg)
    return render(request, 'student_portal/conversation_messaging/edit_message.html', {'form': form, 'message': msg})


@login_required
def delete_message(request, message_id):
    try:
        msg = CommunicationMessage.objects.get(id=message_id)
        if msg.sender != request.user:
            messages.warning(request, "You are not allowed to delete this message.")
            return redirect('student_portal:ginbox', pk=msg.conversation.id)
    except CommunicationMessage.DoesNotExist:
        messages.error(request, "Message not found.")
        return redirect('student_portal:inbox')  # fallback or adjust

    if request.method == 'POST':
        conversation_id = msg.conversation.id
        msg.delete()
        messages.success(request, "Message deleted successfully.")
        return redirect('student_portal:inbox', pk=conversation_id)

    return render(request, 'student_portal/conversation_messaging/confirm_delete.html', {'message': msg})



@login_required
def inbox(request, pk=None):
    user = request.user
    filter_form = ConversationFilterForm(request.GET or None, user=user)
    filter_value = request.GET.get('conversation', '')

    qs = CommunicationMessage.objects.filter(conversation__participants=user)

    # Apply filtering based on dropdown
    if filter_value == 'all_received':
        qs = qs.filter(recipient=user)
    elif filter_value == 'all_sent':
        qs = qs.filter(sender=user)
    elif filter_value == 'groups':
        qs = qs.filter(conversation__is_group=True)
    elif filter_value.startswith('group_'):
        group_id = filter_value.split('_')[1]
        qs = qs.filter(conversation__id=group_id)
    elif filter_value == 'private':
        qs = qs.filter(conversation__is_group=False)
    elif filter_value.startswith('user_'):
        user_id = filter_value.split('_')[1]
        qs = qs.filter(
            conversation__is_group=False,
            conversation__participants__id=user_id
        )

    # Show only one message per conversation (latest)
    latest_msgs = (
        qs
        .select_related("sender", "conversation", "reply_to")
        .order_by("conversation", "-timestamp")
        .distinct("conversation")
    )

    unread_counts = (
        CommunicationMessage.objects
        .filter(is_read=False, recipient=user)
        .values('conversation')
        .annotate(count=models.Count('id'))
    )
    unread_count_map = {item['conversation']: item['count'] for item in unread_counts}

    paginator = Paginator(latest_msgs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Handle selected conversation view and reply
    selected_conversation = None
    if pk:
        selected_conversation = get_object_or_404(Conversation, pk=pk, participants=user)
        selected_conversation.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        if request.method == "POST":
            form = ReplyMessageForm(request.POST, request.FILES)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.sender = user
                msg.conversation = selected_conversation
                if not selected_conversation.is_group:
                    recipient_qs = selected_conversation.participants.exclude(id=user.id)
                    if recipient_qs.exists():
                        msg.recipient = recipient_qs.first()
                reply_to_id = request.POST.get('reply_to')
                if reply_to_id:
                    try:
                        reply_msg = CommunicationMessage.objects.get(id=reply_to_id, conversation=selected_conversation)
                        msg.reply_to = reply_msg
                    except CommunicationMessage.DoesNotExist:
                        pass

                msg.save()
                return redirect("student_portal:inbox", pk=pk)
        else:
            form = ReplyMessageForm()
    else:
        form = ReplyMessageForm()

    return render(request, "student_portal/conversation_messaging/chat_two_pane.html", {
        "page_obj": page_obj,
        "selected_conversation": selected_conversation,
        "form": form,
        "filter_form": filter_form,
        'unread_count_map':unread_count_map
    })


#=========================== Online Payment =====================================


def choose_fee_and_generate_invoice(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "No student profile found for your account.")
        return redirect('student_portal:student_landing_page')  

    enrollment = student.enrolled_students.order_by('-academic_year').first()
    if not enrollment or not enrollment.feestructure:
        messages.warning(request, 'No fee structure defined for this student.')
        return redirect('student_portal:payment_status_view')

    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year


    paid_months = list(
        Payment.objects.filter(
            student=student,
            academic_year=academic_year,
            monthly_tuition_fee_payment_status='paid'
        ).exclude(month__isnull=True)
        .values_list('month', flat=True)
    )
    due_months_choices = [
        (i, date(1900, i, 1).strftime('%B'))
        for i in range(1, 13) if i not in paid_months
    ]

  
    all_admission_fee_items = AdmissionFee.objects.filter(
        admission_fee_policy=fee_structure.admissionfee_policy
    )
    paid_item_ids = AdmissionFeePayment.objects.filter(
        payment__student=student
    ).values_list('admission_fee_item_id', flat=True)

    due_admission_fee_items = all_admission_fee_items.exclude(id__in=paid_item_ids)

    if request.method == 'POST':
        form = FeePaymentForm(
            request.POST,
            student=student,
            tuition_months_choices=due_months_choices
        )
        form.fields['admission_fee_items'].queryset = due_admission_fee_items

        if form.is_valid():
            fee_types = form.cleaned_data['fee_types']
            selected_months = form.cleaned_data.get('tuition_months', [])
            selected_fees = form.cleaned_data.get('admission_fee_items', [])

            total_amount = 0
            description_parts = []

            invoice = PaymentInvoice.objects.create(
                student=student,
                invoice_type='combined',
                amount=0,
                description='',
            )

            # Tuition Fee Calculation
            if 'tuition_fees' in fee_types and selected_months:
                tuition_amount = fee_structure.monthly_tuition_fee
                total_amount += tuition_amount * len(selected_months)
                months_display = ", ".join([date(1900, int(m), 1).strftime('%B') for m in selected_months])
                description_parts.append(f"Tuition Fee for {months_display} {academic_year}")
                invoice.extra_data = {'tuition_months': selected_months}

            # Admission Fee Calculation
            if 'admission_fee' in fee_types and selected_fees:
                adm_amount = sum([item.amount for item in selected_fees])
                total_amount += adm_amount
                invoice.admission_fee_items.set(selected_fees)
                description_parts.append(
                    "Admission Fee: " + ", ".join([item.get_fee_type_display() for item in selected_fees])
                )

            invoice.amount = total_amount
            invoice.description = "; ".join(description_parts)
            invoice.save()

            return redirect(f"/student_portal/payment/initiate/?tran_id={invoice.tran_id}")
        else:
            messages.error(request, "Failed to generate invoice.")
    else:
        form = FeePaymentForm(
            student=student,
            tuition_months_choices=due_months_choices
        )
        form.fields['admission_fee_items'].queryset = due_admission_fee_items

    return render(request, 'student_portal/select_fee_type.html', {'form': form})





def initiate_payment(request):
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    client = request.tenant       
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
    base_url = sslcommerz.base_url or "https://sandbox.sslcommerz.com"  # fallback
   

    if not tran_id:
        return HttpResponse("Missing transaction ID.")

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

    if tuition_months:
        for month in tuition_months:
            payment, _ = Payment.objects.get_or_create(
                academic_year=enrollment.academic_year,
                student=student,
                month=int(month)
            )
            payment.monthly_tuition_fee_paid = enrollment.feestructure.monthly_tuition_fee
            payment.monthly_tuition_fee_payment_status = "paid"
            payment.transaction_id = tran_id
            payment.payment_method = "sslcommerz"
            payment.payment_status = "paid"
            payment.save()



    if invoice.invoice_type == "admission_fee" or "admission" in invoice.description.lower():
        payment_month = invoice.created_at.month
        payment, _ = Payment.objects.get_or_create(
            academic_year=enrollment.academic_year,
            student=student,
            month=payment_month
        )



        session_total = 0
        for item in invoice.admission_fee_items.all():
            AdmissionFeePayment.objects.create(
                payment=payment,
                admission_fee_item=item,
                amount_paid=item.amount,
                payment_status='paid'
            )
            session_total += item.amount

  
        total_paid = AdmissionFeePayment.objects.filter(
            payment__student=student,
            payment__academic_year=enrollment.academic_year
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        all_fee_items = AdmissionFee.objects.filter(
            admission_fee_policy=enrollment.feestructure.admissionfee_policy
        )
        total_due = all_fee_items.aggregate(total=Sum('amount'))['total'] or 0

        if total_paid >= total_due:
            payment.admission_fee_payment_status = 'paid'
        elif total_paid > 0:
            payment.admission_fee_payment_status = 'partial-paid'
        else:
            payment.admission_fee_payment_status = 'due'

        payment.admission_fee_paid = total_paid
        payment.transaction_id = tran_id
        payment.payment_method = "sslcommerz"
        payment.payment_status = "paid"
        payment.save()
   
        for item in invoice.admission_fee_items.all():
            AdmissionFeePayment.objects.get_or_create(
                payment=payment,
                admission_fee_item=item,
                amount_paid=item.amount,
                payment_status='paid'
            )

    invoice.is_paid = True
    invoice.save()

    return redirect('student_portal:post_payment_redirect', invoice_id=invoice.id)




def post_payment_redirect(request, invoice_id):
    invoice = get_object_or_404(PaymentInvoice, id=invoice_id)
    student = invoice.student

    if invoice.invoice_type == 'consultation':
        return render(request, 'student_portal/thank_you_consultation.html', {'student': student})
    elif invoice.invoice_type == 'labtest':
        return render(request, 'student_portal/thank_you_lab.html', {'invoice': invoice})
    return render(request, 'student_portal/thank_you_generic.html', {'invoice': invoice})



@csrf_exempt
def payment_fail(request):
    return HttpResponse("Payment failed!")

@csrf_exempt
def payment_cancel(request):
    return HttpResponse("Payment cancelled by user.")





##################### new payment method for online payment #######################


@login_required
def payment_invoice_detail(request, pk):
    invoice = get_object_or_404(PaymentInvoice, pk=pk)
    student = invoice.student
    remaining_due = get_due_till_today(student)  

    today = date.today()

    due_month = today.month
    if today.day < 25:
        due_month -= 1
    due_month = max(due_month, 0)

    fee_breakdown = []

    if hasattr(invoice, 'tuition_payments') and invoice.tuition_payments.exists():
        entity_qs = invoice.tuition_payments.filter(student=invoice.student)
        entity_paid_in_this_invoice = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
       
        all_entity_qs = invoice.student.student_tuition_payments.filter(month__lte=due_month)
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Tuition Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today': entity_paid_in_this_invoice,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })


    if hasattr(invoice, 'admission_payments') and invoice.admission_payments.exists():
        entity_qs = invoice.admission_payments.filter(student=invoice.student)
        entity_paid_today = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0       

        all_entity_qs = invoice.student.student_admission_payments.filter(month__lte=due_month)
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Admission Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today':entity_paid_today,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })


    if hasattr(invoice, 'transport_payments') and invoice.transport_payments.exists():
        entity_qs = invoice.transport_payments.filter(student=invoice.student)
        entity_paid_today = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
       
        all_entity_qs = invoice.student.student_transport_payments.filter(month__lte=due_month)
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Admission Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today':entity_paid_today,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })


    if hasattr(invoice, 'hostel_payments') and invoice.hostel_payments.exists():
        entity_qs = invoice.hostel_payments.filter(student=invoice.student)
        entity_paid_today = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
       
        all_entity_qs = invoice.student.student_hostel_payments.filter(month__lte=due_month)
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Admission Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today':entity_paid_today,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })


    if hasattr(invoice, 'exam_payments') and invoice.exam_payments.exists():
        entity_qs = invoice.exam_payments.filter(student=invoice.student)
        entity_paid_today = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
      
        all_entity_qs = invoice.student.student_exam_fee_payments.all()
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Admission Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today':entity_paid_today,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })

    if hasattr(invoice, 'other_payments') and invoice.other_payments.exists():
        entity_qs = invoice.other_payments.filter(student=invoice.student)
        entity_paid_today = entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        all_entity_qs = invoice.student.other_fee_students.all()
        total_due = all_entity_qs.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_entity_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        fee_breakdown.append({
            'label': 'Admission Fee',
            'total': total_due,
            'paid': total_paid,
            'due': max(total_due - total_paid, 0),
            'status': 'paid' if total_paid >= total_due else 'partial',
            'paid_today':entity_paid_today,
            'date': invoice.created_at,
            'method': invoice.payment_method or 'Cash',
        })

    total_paid = sum(f['paid'] for f in fee_breakdown)
    total_due = sum(f['due'] for f in fee_breakdown)
    total_amount = sum(f['total'] for f in fee_breakdown)

    context = {
        'invoice': invoice,
        'remaining_due': remaining_due,
        'fee_breakdown': fee_breakdown,
        'total_paid': total_paid,
        'total_due': total_due,
        'total_amount': total_amount,
    }

    return render(request, 'student_portal/online_payment/payment_invoice_detail.html', context)


def payment_invoice_list(request):
    q = request.GET.get('q', '')
    invoices = PaymentInvoice.objects.select_related('student').order_by('-created_at')
    if q:
        invoices = invoices.filter(
            Q(student__name__icontains=q) | Q(student__student_id__icontains=q)
        )
    return render(request, 'student_portal/online_payment/payment_invoice_list.html', {'invoices': invoices, 'q': q})



def payment_invoice_receipt(request, pk):
    invoice = get_object_or_404(PaymentInvoice, pk=pk)
    student = invoice.student
    enrollment = getattr(invoice, 'student_enrollment', None)
    class_name = getattr(enrollment, 'student_class', 'N/A')

    # Collect payment breakdowns (safely handle missing records)
    fee_breakdown = []

    def safe_get(payment_qs, label):
        payment = payment_qs.first()
        if payment and (payment.amount_paid or 0) > 0:
            fee_breakdown.append({
                "label": label,
                "total": getattr(payment, 'total_amount', payment.total_amount),
                "paid": payment.amount_paid,
                "due": getattr(payment, 'due_amount', 0),
                "status": "Paid" if getattr(payment, 'payment_status', '').lower() == 'paid' else "Partial" if getattr(payment, 'due_amount', 0) > 0 else "Due"
            })

    # Fetch and append each payment type if exists
    safe_get(student.student_tuition_payments, "Tuition Fee")
    safe_get(student.student_admission_payments, "Admission Fee")
    safe_get(student.student_transport_payments, "Transport Fee")
    safe_get(student.student_hostel_payments, "Hostel Fee")
    safe_get(student.student_exam_fee_payments, "Exam Fee")
    safe_get(student.other_fee_students, "Other Fee")

    # Fallback if no breakdown found
    if not fee_breakdown:
        fee_breakdown.append({
            "label": invoice.description or "General Payment",
            "total": invoice.amount or 0,
            "paid": invoice.paid_amount or 0,
            "due": invoice.due_amount or 0,
            "status": "Paid" if invoice.is_paid else "Partial" if (invoice.due_amount or 0) > 0 else "Due"
        })

    # Prepare PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- Header ---
    school_name = "🏫 My School Name"
    address = "School Road, City"
    contact = "Phone: +8801XXXXXXXXX"

    header_data = [
        [school_name, "", f"Receipt No: {invoice.tran_id}"],
        [address, "", f"Date: {invoice.created_at.strftime('%d-%b-%Y')}"],
        [contact, "", f"Invoice Type: {invoice.get_invoice_type_display()}"],
    ]
    header_table = Table(header_data, colWidths=[250, 200, 200])
    header_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('ALIGN', (2, 0), (2, 2), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # --- Title ---
    title = Paragraph("<b>MONEY RECEIPT</b>", ParagraphStyle('title', fontSize=18, alignment=1, spaceAfter=10))
    elements.append(title)
    elements.append(Spacer(1, 10))

    # --- Student Info ---
    student_info = [
        ["Student Name", student.name],
        ["Student ID", student.student_id],
        ["Class", class_name],
        ["Guardian", getattr(student, 'guardian_name', 'N/A')],
    ]
    student_table = Table(student_info, colWidths=[150, 300])
    student_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 15))

    # --- Fee Table ---
    fee_data = [["Description", "Total Amount", "Paid", "Due", "Status"]]
    for f in fee_breakdown:
        fee_data.append([
            f["label"],
            f"{f['total']:.2f}",
            f"{f['paid']:.2f}",
            f"{f['due']:.2f}",
            f["status"]
        ])

    # Add Total row
    total_paid = sum(f["paid"] for f in fee_breakdown)
    total_due = sum(f["due"] for f in fee_breakdown)
    total_amount = sum(f["total"] for f in fee_breakdown)
    fee_data.append(["<b>Total</b>", f"{total_amount:.2f}", f"{total_paid:.2f}", f"{total_due:.2f}", ""])

    fee_table = Table(fee_data, colWidths=[300, 100, 100, 100, 120])
    fee_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(fee_table)
    elements.append(Spacer(1, 25))

    # --- Footer / Signature ---
    footer_data = [
        ["Received By", "", "Signature of Student/Guardian"],
        ["__________________", "", "__________________"],
    ]
    footer_table = Table(footer_data, colWidths=[200, 200, 200])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(footer_table)
    elements.append(Spacer(1, 15))

    note = Paragraph("<i>Thank you for your payment!</i>", styles['Normal'])
    elements.append(note)

    # --- Build PDF ---
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"MoneyReceipt_{student.name}_{invoice.invoice_type}_{invoice.id}.pdf"
    response['Content-Disposition'] = f'inline; filename=\"{filename}\"'
    return response




@login_required
def ajax_pending_admission_fees(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    enrollment = student.enrolled_students.select_related(
        'feestructure__admissionfee_policy'
    ).first()

    today = date.today()
    due_month = today.month
    if today.day < 25:
        due_month -= 1
    due_month = max(due_month, 0)

    if not enrollment or not enrollment.feestructure:
        return JsonResponse({
            "pending_items": [],
            "paid_items": [],
            "total_pending": "0.00"
        })

    policy_items = enrollment.feestructure.admissionfee_policy.admission_fees.all()  
    payments = AdmissionFeePayment.objects.filter(
        student=student,
        admission_fee_assignment__admission_fee__in=policy_items)

    pending_items = []
    paid_items = []
    total_pending = Decimal("0.00")

    for item in policy_items:
        if item.due_month > due_month:
            continue

        item_payments = payments.filter(
            admission_fee_assignment__admission_fee=item)
        total_paid = (
            item_payments.aggregate(total=Sum('amount_paid'))['total']
            or Decimal('0.00'))

        remaining = item.amount - total_paid     
        if total_paid > 0:
            last_payment = item_payments.last()
            paid_items.append({
                "name": item.fee_type,
                "amount": str(total_paid),
                "date": last_payment.payment_date.strftime("%d %b %Y")})
   
        if remaining > 0:
            pending_items.append({
                "id": item.id,
                "name": item.fee_type,
                "amount": str(remaining)})
            total_pending += remaining

    return JsonResponse({
        "pending_items": pending_items,
        "paid_items": paid_items,
        "total_pending": str(total_pending)
    })


################################# Online Payment ######################################

def review_and_payfees_online(request):
    students = Student.objects.all()
    student_id = request.GET.get('student_id')
    student = None
    dues = {}
    total_due = Decimal('0')

    if student_id:
        student = Student.objects.filter(id=student_id).first()
    else:
        student = Student.objects.filter(user=request.user).first()

    if not student:
        messages.error(request, "Invalid student selected.")
        return redirect('student_portal:payment_status_view')

    dues = get_due_till_today(student)

    total_due = sum(
        Decimal(data.get('net_due', 0))
        for data in dues.values())

    if total_due <= 0:
        messages.warning(request, "No dues found for this student.")
        return redirect('student_portal:payment_status_view')

    if request.method == "POST":
        selected_types = request.POST.getlist('fee_types')
        entered_amount = Decimal(
            request.POST.get('custom_amount', '0') or '0')

        if not selected_types:
            messages.warning(request, "Please select at least one payment type.")
            return redirect(f"{request.path}?student_id={student.id}")

        selected_dues = {
            ft: dues[ft]['net_due']
            for ft in selected_types
            if ft in dues and dues[ft].get('net_due', 0) > 0}

        total_selected_due = sum(
            Decimal(v) for v in selected_dues.values() )

        if total_selected_due <= 0:
            messages.warning(request, "No due to pay for selected categories.")
            return redirect(f"{request.path}?student_id={student.id}")
 
        total_payment_amount = (
            min(entered_amount, total_selected_due)
            if entered_amount > 0
            else total_selected_due
        )

        if total_payment_amount <= 0:
            messages.warning(request, "Please enter a valid payment amount.")
            return redirect(f"{request.path}?student_id={student.id}")     
        
        transaction_id = f"TXN-{uuid.uuid4().hex[:10]}"
        ssl_store_id = getattr(settings, 'SSLZCOMMERZ_STORE_ID', None)
        ssl_store_passwd = getattr(settings, 'SSLZCOMMERZ_STORE_PASS', None)

        ssl_api_url = (
            "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            if settings.SSLZCOMMERZ_IS_SANDBOX
            else "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
        )

        if not (ssl_store_id and ssl_store_passwd):
            messages.error(request, "SSLCommerz credentials not configured properly.")
            return redirect(f"{request.path}?student_id={student.id}")

        post_data = {
            'store_id': ssl_store_id,
            'store_passwd': ssl_store_passwd,
            'total_amount': float(total_payment_amount),
            'currency': "BDT",
            'tran_id': transaction_id,
            'success_url': request.build_absolute_uri('/student_portal/ssl-success/'),
            'fail_url': request.build_absolute_uri('/payments/payment/fail/'),
            'cancel_url': request.build_absolute_uri('/payments/payment/cancel/'),
            'cus_name': student.name,
            'cus_email': student.email or 'noemail@school.com',
            'cus_phone': student.phone_number or 'N/A',
            'cus_add1': "Dhaka",
            'cus_city': "Dhaka",
            'cus_country': "Bangladesh",
            'shipping_method': "NO",
            'value_a': str(student.id),
            'value_b': ','.join(selected_dues.keys()),
            'value_c': str(total_payment_amount),
            'product_category': 'School Fees',
            'product_name': 'Multi-Fee Payment',
            'product_profile': "general",
        }

        try:
            response = requests.post(ssl_api_url, data=post_data, timeout=15)
            res_json = response.json()
        except Exception as e:
            messages.error(request, f"SSLCommerz connection error: {e}")
            return redirect(f"{request.path}?student_id={student.id}")

        if res_json.get('status') == 'SUCCESS' and res_json.get('GatewayPageURL'):
            return redirect(res_json['GatewayPageURL'])
        else:
            messages.error(
                request,
                f"SSLCommerz Error: {res_json.get('failedreason', 'Unknown error')}"
            )
            return redirect(f"{request.path}?student_id={student.id}")

    return render(
        request,
        'student_portal/online_payment/review_and_payonline.html',
        {
            'all_students': students,
            'student': student,
            'dues': dues,
            'total_due': total_due,
        }
    )



@csrf_exempt
def ssl_success(request):
    data = request.POST
    student_id = data.get('value_a')
    payment_types = data.get('value_b', '').split(',')

    student = Student.objects.filter(id=student_id).first()
    if not student:
        messages.error(request, "Student not found.")
        return redirect('student_portal:payment_status_view')
    total_amount = Decimal(data.get('value_c') or data.get('amount', 0))
    remaining_amount = total_amount
    applied_payments = []
  
    dues = get_due_till_today(student)

    for fee_type in payment_types:
        if remaining_amount <= 0:
            break
        if fee_type not in dues:
            continue
        fee_due = dues[fee_type].get('net_due', 0)
        if fee_due <= 0:
            continue

        pay_for_this_fee = min(fee_due, remaining_amount)

        if fee_type in ['tuition', 'hostel', 'transport', 'admission']:
            _, updated_items = apply_payment_to_oldest_months(
                student, fee_type, pay_for_this_fee)
        else:
            _, updated_items = apply_one_time_payment(
                student, fee_type, pay_for_this_fee)

        applied_payments.extend(updated_items)
        remaining_amount -= pay_for_this_fee  

    if applied_payments:
        invoice = create_payment_invoice(
            applied_payments,
            invoice_type=payment_types,
            payment_method='SSLCOMMERZE',
            entered_amount=total_amount
        )
        messages.success(
            request,
            f"Payment successful. Invoice #{invoice.id} created."
        )      
        return redirect('payments:payment_invoice_detail', pk=invoice.pk)

    messages.warning(
        request,
        "Payment received but no dues were applicable.")
    return redirect('student_portal:payment_status_view')

