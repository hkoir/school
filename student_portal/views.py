
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from student_portal.forms import ExamResultForm
from results.models import Result,StudentFinalResult,Grade
from results.utils import aggregate_student_data,calculate_gpa_and_grade
from django.db.models import Max, Count
from collections import defaultdict


from django.core.paginator import Paginator
from datetime import timedelta
from datetime import datetime
from django.contrib import messages
from collections import defaultdict
from django.utils.timezone import now
from datetime import date
import json
from collections import Counter



from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageTemplate
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
import os
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4,letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from decimal import Decimal
from django.db.models import Sum, F
import base64




from students.models import StudentEnrollment
from school_management.models import Subject,Schedule
from payments.models import Payment
from.forms import StudentAttendanceFilterForm,AcademicYearFilterForm
from results.models import ExamType
from attendance.forms import AttendanceFilterForm
from attendance.models import Attendance
from students.models import Student
from students .models import  Student
from core.models import Notice,Employee
from core.forms import NoticeForm
from collections import defaultdict
from django.db.models import Max, Count



def student_landing_page(request):
    return render(request,'student_portal/student_landing_page.html')




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



@login_required
def student_exam_schedule2(request):
    student = Student.objects.filter(user = request.user).first()

    exam_types = ExamType.objects.filter(
        exam_results__student=student
    ).distinct().order_by('exam_date')

    exam_status = []
    for exam in exam_types:
        exam_status.append({
            "exam": exam,
            "fees_clear": has_cleared_required_fees(student, exam.exam_date)
        })

    return render(request, "student_portal/student_exam_list.html", {
        "student": student,
        "exam_types": exam_types,
        "exam_status": exam_status,
    })


@login_required
def student_exam_schedule(request):
    student = Student.objects.filter(user=request.user).first()
    
    enrollment = StudentEnrollment.objects.filter(student=student).first()
    if enrollment:
        enrolled_subjects = enrollment.subjects.all()       

    if not enrollment:
        return render(request, "student_portal/student_exam_list.html", {
            "student": student,
            "exam_types": [],
            "exam_status": [],
        })

    enrolled_subjects = enrollment.subjects.all()   
    exam_types = ExamType.objects.filter(
        subject__in=enrolled_subjects,
        exam__academic_year=enrollment.academic_year,
      
       
    ).distinct().order_by('exam_date') 

    exam_status = []
    for exam in exam_types:
        exam_status.append({
            "exam": exam,
            "fees_clear": has_cleared_required_fees(student, exam.exam_date)
        })

    return render(request, "student_portal/student_exam_list.html", {
        "student": student,
        "exam_types": exam_types,
        "exam_status": exam_status,
    })


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
def preview_admit_card(request, exam_id):   
    student=Student.objects.filter(user=request.user).first()
    exam_type = get_object_or_404(ExamType, id=exam_id)
    exam_date = exam_type.exam_date

    cleared_fees, total_due = has_cleared_required_fees(student, exam_date)

#    if not cleared_fees:
 #       return render(request, "student_portal/admit_card_blocked.html", {
  #          "message": "You cannot download the admit card until all dues are cleared up to the exam date.",
   #         "total_due": total_due
    #    })

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
    exam = None

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

    total_paid = Payment.objects.filter(
        student=student,
        academic_year=academic_year
    ).aggregate(total=Sum('admission_fee_paid'))['total'] or Decimal('0.00')

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
    today = date.today()
    current_month = today.month
    enrollment = student.enrolled_students.first()
    fee_structure = enrollment.feestructure
    academic_year = enrollment.academic_year
    monthly_fee = fee_structure.monthly_tuition_fee
    total_due_amount = monthly_fee * current_month
    total_paid_amount = student.student_payments.filter(academic_year=academic_year).aggregate(
        total_paid=Sum('monthly_tuition_fee_paid')
    )['total_paid'] or 0
    return total_due_amount, total_paid_amount




def payment_status_view(request):
    form = AcademicYearFilterForm(request.GET or None)
    academic_year = None
    total_due_amount = Decimal('0.00')
    total_paid_amount = Decimal('0.00')
    data = []
    months = [date(1900, i, 1).strftime('%B') for i in range(1, 13)]
    payment_status_data = {}

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
            total_due, total_paid = calculate_due_and_paid(student)

            total_due_amount += total_due
            total_paid_amount += total_paid

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
    }
    form = AcademicYearFilterForm()
    return render(request, 'student_portal/payment_status.html', context)






from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from school_management.models import Schedule, AcademicClass, Section
from datetime import datetime,timedelta
from students.models import Student
from django.core.exceptions import PermissionDenied



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
    gender = section.class_gender
    academic_year = enrollment.academic_year
    shift = enrollment.student_class.shift
    version = enrollment.student_class.language_version

    # Get day from query params
    day_filter = request.GET.get('day')  # e.g., "Monday"

    # Base queryset
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
        'subject_assignment__class_room'
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

from messaging.models import CommunicationMessage,Conversation,MessageReadStatus
from messaging.forms import CommunicationMessageForm
from accounts.models import CustomUser
from django.db.models import OuterRef, Subquery, Q,Count
from messaging.forms import ReplyMessageForm
#===================================Private messaging #####################################


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
    

    return render(request, 'student_portal/conversation_messaging/send_message.html', {'form': form})





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
    conversation = get_object_or_404(Conversation, pk=pk, is_group=True)
    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id__in=conversation.participants.all())
        conversation.participants.add(*users)
        return redirect('student_portal:group_conversation_detail', pk=conversation.pk)
    available_users = CustomUser.objects.exclude(id__in=conversation.participants.all())
    return render(request, "student_portal/conversation_messaging/add_participants.html", {
        "conversation": conversation,
        "available_users": available_users
    })


@login_required
def remove_participants(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, is_group=True)
    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        conversation.participants.remove(*users)
        return redirect('student_portal:group_conversation_detail', pk=conversation.pk)
    current_participants = conversation.participants.exclude(id=request.user.id)
    return render(request, "student_portal/conversation_messaging/remove_participants.html", {
        "conversation": conversation,
        "current_participants": current_participants
    })





@login_required
def edit_message(request, message_id):
    message = get_object_or_404(CommunicationMessage, id=message_id, sender=request.user)
    if request.method == 'POST':
        form = ReplyMessageForm(request.POST, request.FILES, instance=message)
        if form.is_valid():
            form.save()
            return redirect('student_portal:group_conversation_detail', pk=message.conversation.id)
    else:
        form = ReplyMessageForm(instance=message)
    return render(request, 'student_portal/conversation_messaging/edit_message.html', {'form': form, 'message': message})


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(CommunicationMessage, id=message_id, sender=request.user) 
    if request.method == 'POST':
        conversation_id = message.conversation.id
        message.delete()        
        return redirect('student_portal:group_conversation_detail', pk=conversation_id)
    return render(request, 'student_portal/conversation_messaging/confirm_delete.html', {'message': message})







from messaging.forms import ConversationFilterForm

from collections import defaultdict
from django.db import models

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



