from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import qrcode
from openpyxl import Workbook
from io import BytesIO
from django.utils import timezone
import os
import base64

from reportlab.lib import colors
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4,letter
from reportlab.pdfgen import canvas
from django.conf import settings
from reportlab.lib.pagesizes import A5, landscape

from collections import defaultdict
from datetime import datetime,timedelta
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from teachers.models import Teacher
from .models import (
    ExamFee, ExamFeeAssignment, TransportRoute, TransportAssignment,
    RoomType, Hostel, HostelRoom, HostelAssignment, OtherFee,
    Student, StudentEnrollment,TuitionFeeAssignment,AdmissionFeeAssignment,Guardian
)
from results.models import Exam,ExamType
from .forms import (
    ExamFeeForm, ExamFeeAssignmentForm, TransportRouteForm, TransportAssignmentForm,
    RoomTypeForm, HostelForm, HostelRoomForm, HostelAssignmentForm, OtherFeeForm,
    TuitionAssignmentForm,AdmissionAssignmentForm,StudentFilterForm,
    StudentEnrollmentForm,GuardianForm,StudentForm
)
from school_management.models import Schedule, AcademicClass, Section,Subject
from core.models import Employee

from django.contrib import messages
from django.shortcuts import redirect, render
from decimal import Decimal
from datetime import date
from django.http import JsonResponse
from payments.models import FeeStructure,OtherFeePayment
from school_management.models import AcademicClass
from payments.utils import get_due_till_today
from django.db.models import Q,F



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
        return redirect('students:create_student_enrollment')  
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



def student_subject_enrollment_view(request,student_id):
    student =  get_object_or_404(Student,id=student_id)
    enrollment = student.enrolled_students.first()
    academic_class = enrollment.academic_class
    subjects = academic_class.subjects.all()
    context = {
    "student": student,
    "academic_class": academic_class,
    "subjects": subjects}

    return render(request,'students/student_subject_assignment_view.html',context)



@login_required
def school_class_routine_view(request):   
    user = request.user
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    student = None
    teacher = None
    student_id = request.GET.get('student_id')
    teacher_id = request.GET.get('teacher_id')

    if teacher_id:        
        teacher = get_object_or_404(Teacher, id=teacher_id)
    elif student_id:        
        student = get_object_or_404(Student, id=student_id)
    else:        
        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            try:
                teacher = Teacher.objects.get(user=user)
            except Teacher.DoesNotExist:
                pass 

    if student:
        enrollment = student.enrolled_students.first()
        if not enrollment:
            return render(request, 'students/no_student.html', {"message": "No enrollment found."})

        schedules_qs = Schedule.objects.filter(
            academic_class=enrollment.academic_class,
            shift=enrollment.shift,
            gender=enrollment.gender,
            language=enrollment.language,
            section=getattr(enrollment, 'section', None)
        ).order_by('day_of_week', 'start_time')

        title = f"{student.user.get_full_name()} - Class Routine"

    elif teacher:
        schedules_qs = Schedule.objects.filter(
            subject_teacher=teacher
        ).order_by('day_of_week', 'start_time')
        title = f"{teacher.name} - Teaching Schedule"

    time_list = sorted({(s.start_time, s.end_time) for s in schedules_qs})
    time_slots = [{"id": i, "start": t[0].strftime("%H:%M"), "end": t[1].strftime("%H:%M")}
                  for i, t in enumerate(time_list)]

    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    schedule_map = {day: {i: [] for i in range(len(time_slots))} for day in days}

    color_classes = ["class-subject-0","class-subject-1","class-subject-2",
                     "class-subject-3","class-subject-4","class-subject-5","class-subject-6"]
    for s in schedules_qs:
        slot_id = next(i for i, t in enumerate(time_list) if t == (s.start_time, s.end_time))
        s.color_class = color_classes[hash(s.subject.id) % len(color_classes)]
        schedule_map[s.day_of_week][slot_id].append(s)

    context = {
        "title": title,
        "student": student,
        "teacher": teacher,
        "students": students,
        'teachers':teachers,
        "days": days,
        "time_slots": time_slots,
        "schedule_map": schedule_map
    }

    return render(request, "students/student_class_routine_view.html", context)





def student_id_card_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'students/student_id_card.html', {
        'student': student,
        'school_logo_url': student.school.logo.url if student.school.logo else '',
    })




from school_management.models import School,Shift,Language,Section,Gender
from university_management.models import Program,AcademicSession,LanguageVersion

def student_id_card_print(request):
    students = Student.objects.all()

    # dropdown datasets
    academic_classes = AcademicClass.objects.all()
    shifts = Shift.objects.all()
    genders = Gender.objects.all()
    languages = Language.objects.all()
    sections = Section.objects.all()

    programs = Program.objects.all()
    language_versions = LanguageVersion.objects.all()

    school = School.objects.first()

    # ===== SCHOOL FILTERS =====
    academic_class_id = request.GET.get('academic_class_id')
    shift_id = request.GET.get('shift_id')
    gender_id = request.GET.get('gender_id')
    language_id = request.GET.get('language_id')
    section_id = request.GET.get('section_id')

    if academic_class_id:
        students = students.filter(enrolled_students__academic_class_id=academic_class_id)

    if shift_id:
        students = students.filter(enrolled_students__shift_id=shift_id)

    if gender_id:
        students = students.filter(enrolled_students__gender_id=gender_id)

    if language_id:
        students = students.filter(enrolled_students__language_id=language_id)

    if section_id:
        students = students.filter(enrolled_students__section_id=section_id)

    # ===== VARSITY FILTERS =====
    program_id = request.GET.get('program_id')
    language_version_id = request.GET.get('language_version_id')

    if program_id:
        students = students.filter(varsity_student_enrollments__program_id=program_id)

    if language_version_id:
        students = students.filter(varsity_student_enrollments__language_version_id=language_version_id)

    students = students.distinct()

    context = {
        'students': students,
        'school_logo_url': school.logo.url if school and school.logo else '',
        'academic_classes': academic_classes,
        'shifts': shifts,
        'genders': genders,
        'languages': languages,
        'sections': sections,
        'programs': programs,
        'language_versions': language_versions,
    }
    return render(request, 'students/student_id_card_print.html', context)



def download_student_id_card(request, student_id):
    student = Student.objects.get(id=student_id)
    enrollment = student.enrolled_students.select_related(
        "academic_class__faculty__school"
    ).first()

    varsity_enrollment = student.varsity_student_enrollments.select_related(
        "program__department__faculty__school"
    ).first()

    school = enrollment.academic_class.faculty.school or varsity_enrollment.program.department.faculty.school
    CARD_W = 85.6 * mm
    CARD_H = 54.0 * mm

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{student.student_id}_idcard.pdf"'
    c = canvas.Canvas(response, pagesize=(CARD_W, CARD_H))

    # ================================
    #  >>>>>>> FRONT PAGE <<<<<<<<<<
    # ================================
    c.setFillColor(colors.whitesmoke)
    c.rect(0, 0, CARD_W, CARD_H, fill=1)

    if school.logo:
        logo = ImageReader(school.logo.path)
        c.drawImage(logo, 4*mm, CARD_H - 20*mm, 16*mm, 16*mm, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawCentredString(CARD_W/2, CARD_H - 5*mm, school.name.upper())

    if student.profile_picture:
        photo = ImageReader(student.profile_picture.path)
        c.drawImage(photo, CARD_W - 22*mm, CARD_H - 28*mm, 18*mm, 22*mm, mask='auto')
    else:
        c.setFont("Helvetica", 8)
        c.drawString(CARD_W - 22*mm, CARD_H - 10*mm, "No Photo")

    y = CARD_H - 22*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(4*mm, y, student.name.title())

    c.setFont("Helvetica", 8)
    y -= 5*mm
    c.drawString(4*mm, y, f"ID: {student.student_id}")

    class_name = enrollment.academic_class.name if enrollment else "—"
    program = varsity_enrollment.program.name if varsity_enrollment else "—"
    y -= 4*mm
    if class_name:
         c.drawString(4*mm, y, f"Class: {class_name}")
    if program:
         c.drawString(4*mm, y, f"Program: {program}")

    y -= 4*mm
    c.drawString(4*mm, y, f"DOB: {student.date_of_birth.strftime('%d-%b-%Y')}")

    y -= 4*mm
    c.drawString(4*mm, y, f"Gender: {student.gender}")

    y -= 4*mm
    c.drawString(4*mm, y, f"Phone: {student.phone_number}")

    qr_data = f"STUDENT-ID:{student.student_id}"
    qr = qrcode.make(qr_data)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_img = ImageReader(buf)
   
    c.drawImage(qr_img, CARD_W - 20*mm, CARD_H - 48*mm, 18*mm, 18*mm, mask='auto')

    # Footer
    c.setFillColor(colors.darkblue)
    c.rect(0, 0, CARD_W, 6*mm, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(CARD_W/2, 2*mm, "STUDENT ID CARD")

    c.showPage()

    # ================================
    #  >>>>>>> BACK PAGE <<<<<<<<<<
    # ================================
    c.setFillColor(colors.whitesmoke)
    c.rect(0, 0, CARD_W, CARD_H, fill=1)

    # Watermark Logo
    if school.logo:
        wm = ImageReader(school.logo.path)
        c.saveState()
        c.translate(CARD_W/2, CARD_H/2)
        c.rotate(30)
        c.setFillAlpha(0.1)
        c.drawImage(wm, -25*mm, -15*mm, 50*mm, 40*mm, mask='auto')
        c.restoreState()

    # Emergency & Info
    issue = date.today()
    expiry = issue + timedelta(days=365)
    blood = getattr(student, "blood_group", "N/A")

    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    y = CARD_H - 8*mm

    c.drawString(4*mm, y, f"Blood Group: {blood}")
    y -= 4*mm
    c.drawString(4*mm, y, f"Emergency: {student.guardian.phone_number}")
    y -= 4*mm
    c.drawString(4*mm, y, f"Address: {student.address[:40]}...")
    y -= 4*mm
    c.drawString(4*mm, y, f"Issue Date: {issue.strftime('%d-%b-%Y')}")
    y -= 4*mm
    c.drawString(4*mm, y, f"Valid Till: {expiry.strftime('%d-%b-%Y')}")

    # Policy
    y -= 6*mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(4*mm, y, "School Policy:")
    y -= 4*mm
    c.setFont("Helvetica", 6.5)
    policy = [
        "• This card is property of the school.",
        "• Must be carried on campus.",
        "• If found, return to school office.",
        "• Misuse is strictly prohibited.",
        "• Non-transferable."
    ]
    for line in policy:
        c.drawString(6*mm, y, line)
        y -= 4*mm

    # Back Footer
    c.setFillColor(colors.darkblue)
    c.rect(0, 0, CARD_W, 6*mm, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(CARD_W/2, 2*mm, f"{school.phone if hasattr(school,'phone') else ''}")

    c.showPage()
    c.save()

    return response





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
        return redirect('students:view_student_vcard')  
    else:
        print(form.errors)
        
    students = Student.objects.all()  
    student_classes = AcademicClass.objects.all() 
    sections = Section.objects.all() 
    subjects = Subject.objects.all()
  

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



def get_student_details(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    
    # Constructing the response
    data = {
        "name": student.name,
        "student_id": student.student_id,
        "class": student.enrolled_students.first().academic_class.name if student.enrolled_students.exists() else "N/A",
        "section": student.enrolled_students.first().section.name if student.enrolled_students.exists() else "N/A",
        "shift": student.enrolled_students.first().shift if student.enrolled_students.exists() else "N/A",
        "gender": student.enrolled_students.first().gender if student.enrolled_students.exists() else "N/A",
        "language_version": student.enrolled_students.first().language if student.enrolled_students.exists() else "N/A",
        'phone_number':student.phone_number if student.phone_number else 'N/A',
        'Email':student.email if student.email else 'N/A',
        'address':student.address if student.address else 'N/A',
        'guardian':student.guardian.name if student.guardian.name else 'N/A',
        'guardian_phone':student.guardian.phone_number if student.guardian.phone_number else 'N/A',
        'guardian_email':student.guardian.email if student.guardian.email else 'N/A',
        'Relationship':student.guardian.relationship if student.guardian.relationship else 'N/A'
    }
    
    return JsonResponse(data)




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
def preview_admit_card(request,exam_id):
    student = get_object_or_404(Student, user=request.user)
    exam_type = get_object_or_404(Exam, id=exam_id)
    exam_date = exam_type.exam_start_date

    # cleared_fees, total_due = has_cleared_required_fees(student, exam_date)

    # if not cleared_fees:
    #     return render(request, "students/admit_card_blocked.html", {
    #         "message": "You cannot download the admit card until all dues are cleared up to the exam date.",
    #         "total_due": total_due
    #     })

    pdf_buffer = generate_admit_card_pdf(student, exam_type)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')

    return render(request, "students/preview_admit_card.html", {
        "student": student,
        "exam_type": exam_type,
        "pdf_preview": pdf_base64,
    })




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

    return render(request, 'exams/exam_schedule.html', context)




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
    gender = enrollment.gender
    academic_year = enrollment.academic_year
    shift = enrollment.shift
    version = enrollment.language
    day_filter = context['day_filter']

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
        base_queryset = base_queryset.filter(academic_class_id=class_id)

    if section_id:
        base_queryset = base_queryset.filter(section_id=section_id)

    if academic_year:
        base_queryset = base_queryset.filter(academic_year=academic_year)

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
        'subject',
        'subject_teacher',
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




###################################### New addition ###########################################


def get_student_enrollments(request, student_id):
    student = Student.objects.filter(id=student_id).first()
    if not student:
        return JsonResponse({"enrollments": []})

    enrollments = StudentEnrollment.objects.filter(student_id=student_id)
    data = [
        {
            "id": e.id,
            "display": f"{student.name} - {e.academic_year} (Enrollment ID: {e.id})"
        }
        for e in enrollments
    ]
    return JsonResponse({"enrollments": data})



def get_student_related_data(request, student_id):
    student = Student.objects.filter(id=student_id).first()
    if not student:
        return JsonResponse({"enrollments": [], "fee_structures": []})

    enrollments = StudentEnrollment.objects.filter(student=student)
    enrollment_data = [
        {
            "id": e.id,
            "display": f"{student.name} - {e.academic_year} ({e.academic_class.name if e.academic_class else 'No Class'})"
        }
        for e in enrollments
    ]

    class_ids = [e.academic_class.id for e in enrollments if e.academic_class]

    fee_structures = FeeStructure.objects.filter(student_class_id__in=class_ids)

    fee_data = [
        {
            "id": f.id,
            "display": f"{f.student_class.name} - {f.language_version or ''} ({f.academic_year})"
        }
        for f in fee_structures
    ]

    return JsonResponse({
        "enrollments": enrollment_data,
        "fee_structures": fee_data
    })




class CRUDMixin:
    template_prefix = ''
    model = None
    form_class = None
    success_url = None

    def get_success_url(self):
        return self.success_url or reverse_lazy(f'{self.template_prefix}_list')

    def form_valid(self, form):
        messages.success(self.request, f"{self.model.__name__} saved successfully.")
        return super().form_valid(form)


class ExamFeeUpdateView(CRUDMixin, UpdateView):
    model = ExamFee
    form_class = ExamFeeForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:exam_fee_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

class ExamFeeDeleteView(DeleteView):
    model = ExamFee
    success_url = reverse_lazy('students:exam_fee_list')
    template_name = 'students/fees/confirm_delete.html'


# ---------- TRANSPORT ROUTE ----------
class TransportRouteListView(ListView):
    model = TransportRoute
    template_name = 'students/fees/transport_route_list.html'
    context_object_name = 'routes'
    paginate_by = 10

class TransportRouteCreateView(CRUDMixin, CreateView):
    model = TransportRoute
    form_class = TransportRouteForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:transport_route_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

class TransportRouteUpdateView(CRUDMixin, UpdateView):
    model = TransportRoute
    form_class = TransportRouteForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:transport_route_list')

class TransportRouteDeleteView(DeleteView):
    model = TransportRoute
    success_url = reverse_lazy('students:transport_route_list')
    template_name = 'students/fees/confirm_delete.html'


# ---------- Tuition Assignment ----------
class TuitionAssignmentListView(ListView):
    model = TuitionFeeAssignment
    template_name = 'students/fees/tuitionassignment_list.html'
    context_object_name = 'tuitions'
    paginate_by = 10

class TuitionAssignmentCreateView(CRUDMixin, CreateView):
    model = TuitionFeeAssignment
    form_class = TuitionAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:tuition_assignment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

class TuitionAssignmentUpdateView(CRUDMixin, UpdateView):
    model = TuitionFeeAssignment
    form_class = TuitionAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:tuition_assignment_list')

class TuitionAssignmentDeleteView(DeleteView):
    model = TuitionFeeAssignment
    success_url = reverse_lazy('students:tuition_assignment_list')
    template_name = 'students/fees/confirm_delete.html'



# ---------- Admission Assignment ----------
class AdmissionAssignmentListView(ListView):
    model = AdmissionFeeAssignment
    template_name = 'students/fees/admission_assignment_list.html'
    context_object_name = 'admission'
    paginate_by = 10

class AdmissionAssignmentCreateView(CRUDMixin, CreateView):
    model = AdmissionFeeAssignment
    form_class = AdmissionAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:admission_assignment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

class AdmissionAssignmentUpdateView(CRUDMixin, UpdateView):
    model = AdmissionFeeAssignment
    form_class = AdmissionAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:tuition_assignment_list')

class AdmissionAssignmentDeleteView(DeleteView):
    model = AdmissionFeeAssignment
    success_url = reverse_lazy('students:transport_assignment_list')
    template_name = 'students/fees/confirm_delete.html'




# ---------- TRANSPORT Assignment ----------
class TransportAssignmentListView(ListView):
    model = TransportAssignment
    template_name = 'students/fees/transportassignment_list.html'
    context_object_name = 'transports'
    paginate_by = 10

class TransportAssignmentCreateView(CRUDMixin, CreateView):
    model = TransportAssignment
    form_class = TransportAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:transport_assignment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

class TransportAssignmentUpdateView(CRUDMixin, UpdateView):
    model = TransportAssignment
    form_class = TransportAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:transport_assignment_list')

class TransportAssignmentDeleteView(DeleteView):
    model = TransportAssignment
    success_url = reverse_lazy('students:transport_assignment_list')
    template_name = 'students/fees/confirm_delete.html'




################## Hostel management ###################################

# ---------- ROOM TYPE ----------
class HostelRoomTypeListView(ListView):
    model = RoomType
    template_name = 'students/fees/roomtype_list.html'
    context_object_name = 'room_type'
    paginate_by = 10



class HostelRoomTypeCreateView(CRUDMixin, CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_room_type_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context
    

class HostelRoomTypeUpdateView(CRUDMixin, UpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_room_type_list')

class HostelRoomTypeDeleteView(DeleteView):
    model = RoomType
    success_url = reverse_lazy('students:hostel_room_type_list')
    template_name = 'students/fees/confirm_delete.html'




# ---------- Hostel ----------
class HostelListView(ListView):
    model = Hostel
    template_name = 'students/fees/hostel_list.html'
    context_object_name = 'hostels'
    paginate_by = 10



class HostelCreateView(CRUDMixin, CreateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context
    

class HostelUpdateView(CRUDMixin, UpdateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_list')

class HostelDeleteView(DeleteView):
    model = Hostel
    success_url = reverse_lazy('students:hostel_list')
    template_name = 'students/fees/confirm_delete.html'




# ---------- Hostel-Room ----------
class HostelRoomlListView(ListView):
    model = HostelRoom
    template_name = 'students/fees/hostelroom_list.html'
    context_object_name = 'hostel_rooms'
    paginate_by = 10



class HostelRoomCreateView(CRUDMixin, CreateView):
    model = HostelRoom
    form_class = HostelRoomForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_room_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context
    

class HostelRoomUpdateView(CRUDMixin, UpdateView):
    model = HostelRoom
    form_class = HostelRoomForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_room_list')

class HostelRoomlDeleteView(DeleteView):
    model = HostelRoom
    success_url = reverse_lazy('students:hostel_list')
    template_name = 'students/fees/confirm_delete.html'




# ---------- Hostel-Room-assignment ----------

class HostelAssignmentlListView(ListView):
    model = HostelAssignment
    template_name = 'students/fees/hostelassignment_list.html'
    context_object_name = 'hostel_assignments'
    paginate_by = 10



class HostelAssignmentCreateView(CRUDMixin, CreateView):
    model = HostelAssignment
    form_class = HostelAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_assignment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context
    

class HostelAssignmentUpdateView(CRUDMixin, UpdateView):
    model = HostelAssignment
    form_class = HostelAssignmentForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:hostel_assignment_list')

class HostelAssignmentDeleteView(DeleteView):
    model = HostelAssignment
    success_url = reverse_lazy('students:hostel_assignment_list')
    template_name = 'students/fees/confirm_delete.html'



######################### other fee model ############################################

def assign_other_fee_by_class(request):
    classes = AcademicClass.objects.all() 
    current_year = date.today().year
    fee_choices = OtherFee.FEE_TYPE_CHOICES

    if request.method == "POST":
        academic_year = int(request.POST.get('academic_year', current_year))
        fee_type = request.POST.get('fee_type')
        amount = Decimal(request.POST.get('amount') or 0)
        description = request.POST.get('description', '')
        target_class_id = request.POST.get('target_class')

        if not all([academic_year, fee_type, amount > 0, target_class_id]):
            messages.error(request, "Please fill in all required fields with valid values.")
            return redirect(request.path)     

        enrollments = StudentEnrollment.objects.filter(academic_class_id=target_class_id, academic_year=academic_year)

        created_count = 0
        for enrollment in enrollments:       
            other_fee, created = OtherFee.objects.get_or_create(
                student = enrollment.student,
                academic_year=academic_year,
                student_enrollment=enrollment,
                fee_type=fee_type,
                defaults={
                    'student': enrollment.student,
                    'amount': amount,
                    'description': description
                }
            )

            payment_exists = OtherFeePayment.objects.filter(
                student=enrollment.student,
                fee_type=fee_type,
                other_fee_assignment=other_fee
            ).exists()

            if not payment_exists:
                OtherFeePayment.objects.create(
                    student=enrollment.student,
                    other_fee_assignment=other_fee,
                    fee_type=fee_type,
                    total_amount=other_fee.amount,
                    due_amount=other_fee.amount,
                    amount_paid=0,
                    payment_status='due',
                    payment_date=None
                )
                created_count += 1

        messages.success(request, f"Other Fee assigned to {created_count} students in the class.")
        return redirect('students:other_fees_list')

    return render(request, 'students/fees/other_fees_by_class.html', {
        'classes': classes,
        'fee_choices': fee_choices,
        'current_year': current_year,
    })



class OtherFeesListView(ListView):
    model = OtherFee
    template_name = 'students/fees/otherfee_list.html'
    context_object_name = 'other_fees'
    paginate_by = 10



class OtherFeesCreateView(CRUDMixin, CreateView):
    model = OtherFee
    form_class = OtherFeeForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:other_fees_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context
    

class OtherFeesUpdateView(CRUDMixin, UpdateView):
    model = OtherFee
    form_class = OtherFeeForm
    template_name = 'students/fees/form.html'
    success_url = reverse_lazy('students:other_fees_list')

class OtherFeesDeleteView(DeleteView):
    model = OtherFee
    success_url = reverse_lazy('students:other_fees_list')
    template_name = 'students/fees/confirm_delete.html'



from decimal import Decimal

def student_dues_overview(request):
    query = request.GET.get('q', '').strip()
    students = Student.objects.all()
    selected_student = None
    dues = {}
    total_due = Decimal('0.00')

    if query:
        students = students.filter(
            Q(name__icontains=query) | Q(student_id__icontains=query)
        )

        if students.count() == 1:
            selected_student = students.first()
            dues = get_due_till_today(selected_student)
            print(dues)

            for fee in dues.values():
                net = fee.get('net_due', 0)
                total_due += Decimal(str(net))
               

    return render(request, 'students/student_dues_overview.html', {
        'students': students[:50],
        'selected_student': selected_student,
        'dues': dues,
        'total_due': total_due,
        'query': query,
    })
