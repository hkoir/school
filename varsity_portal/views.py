
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse,JsonResponse

from university_management.utils import generate_term_invoice_updated,is_fee_cleared,calculate_and_update_term_result

from students.models import Student
from  university_management.models import (   
    StudentSubjectResult,VarsityStudentEnrollment,
    StudentTermResult,SubjectOffering,
    StudentCGPA,ExamRegistration,Program,UniversityFeeStructure,
    AcademicSession,Exam, ExamSchedule,
    Term,UniversityTermInvoice,UniversityPayment,StudentTermRegistration
)

from attendance.models import AttendancePolicy

from university_management.forms import (
    StudentSubjectResultFormSet,UniversityPaymentForm,
    StudentTermRegistrationForm,StudentSubjectEnrollmentForm,StudentSubjectEnrollmentFormSet,
    ExamScheduleForm,StudentEnrollmentForm,ExamForm,ExamScheduleFormSet
)

from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin

from payments.utils import get_due_till_today
from payments.utils import get_due_till_today
from university_management.models import StudentTermResult,StudentCGPA




def student_landing_page(request):
    student = Student.objects.filter(user=request.user).first()
    enrollment = None
    academic_session = None

    if student:
        enrollment = student.varsity_student_enrollments.first()
        if enrollment:
            academic_session = enrollment.academic_session

    student_term_gpa = StudentTermResult.objects.none()
    if academic_session:
        student_term_gpa = StudentTermResult.objects.filter(
            student=student,
            academic_session=academic_session
        )

    student_cgpa = StudentCGPA.objects.filter(
        student=student
    ).first()

    upcoming_exams = Exam.objects.all()
    dues = get_due_till_today(student)
    has_due = any(d['net_due'] > 0 for d in dues.values()) if dues else False

    return render(request, 'varsity_portal/student_landing_page.html', {
        'student': student,
        'student_term_gpa': student_term_gpa,
        'student_cgpa': student_cgpa,
        'upcoming_exams': upcoming_exams,
        'has_due': has_due,
        'enrollment': enrollment,
        'academic_session': academic_session,
    })





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
    return render(request, 'varsity_portal/view_student_vcard.html', 
    {
        'student_records': student_records,
        'form':form,
        'page_obj':page_obj
    })




class StudentEnrollmentCreateView(LoginRequiredMixin, CreateView):
    model = VarsityStudentEnrollment
    form_class = StudentEnrollmentForm
    template_name = 'varsity_portal/enrollment/enrollment_form.html'
    success_url = reverse_lazy('varsity_portal:enrollment_list')

    def form_valid(self, form):
        return super().form_valid(form)


@login_required
def student_enrollment(request):
    try:
        student = get_object_or_404(Student, user=request.user)
    except:
        messages.warning(request,'logged in user is not student')  
        return redirect('varsity_portal:enrollment_list')
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST)

        if form.is_valid():
            program = form.cleaned_data['program']
            language = form.cleaned_data['language']

            fee_structure = get_object_or_404(
                UniversityFeeStructure,
                program=program,
                language=language
            )

            attendance_policy = AttendancePolicy.objects.first()
            enrollment = form.save(commit=False)           
            enrollment.fee_structure = fee_structure
            enrollment.student = student
            enrollment.attendance_policy = attendance_policy
            enrollment.save()

            return redirect('varsity_portal:create_term_registration', enrollment.id)
    else:
        form = StudentEnrollmentForm()

    return render(
        request,
        'varsity_portal/enrollment/enrollment_form.html',
        {'form': form}
    )

def student_enrollment_list(request):
    student = Student.objects.filter(user=request.user).first()
    enrollments = VarsityStudentEnrollment.objects.filter(student = student)
    return render(
        request,
        'varsity_portal/enrollment/enrollment_list.html',{'enrollments':enrollments}
       
    )



class StudentEnrollmentListView(LoginRequiredMixin, ListView):
    model = VarsityStudentEnrollment
    template_name = 'varsity_portal/enrollment/enrollment_list.html'
    paginate_by = 10
    context_object_name = 'enrollments'

    def get_queryset(self):
        queryset = VarsityStudentEnrollment.objects.select_related(
            'student', 'program', 'academic_session'
        ).order_by('-created_at')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(student__student_id__icontains=query)

        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)       
        context['q'] = self.request.GET.get('q', '')
        context['students'] = Student.objects.all().order_by('name')
        return context


from university_management.models import AcademicLevel

@login_required
def term_registration_create(request):
    student = Student.objects.filter(user=request.user).first()
    enrollment = VarsityStudentEnrollment.objects.filter(student=student).first()    
    levels = AcademicLevel.objects.filter(program=enrollment.program)
    terms = Term.objects.none()   
    subject_qs = SubjectOffering.objects.filter(program=enrollment.program)  
    existing_terms = StudentTermRegistration.objects.filter(enrollment=enrollment)
    registered_term_ids = list(existing_terms.values_list('term_id', flat=True))

    if request.method == 'POST':
        term_form = StudentTermRegistrationForm(request.POST)
        formset = StudentSubjectEnrollmentFormSet(request.POST)

        if term_form.is_valid() and formset.is_valid():
            term = term_form.cleaned_data['term']           
            if term.id in registered_term_ids:
                messages.error(request, f"Term '{term}' is already registered for this student.")
            else:
                with transaction.atomic():                 
                    term_reg = term_form.save(commit=False)
                    term_reg.enrollment = enrollment                    
                    term_reg.academic_year = timezone.now().year
                    term_reg.save()
                
                    formset.instance = term_reg
                    for obj in formset.save(commit=False):
                        obj.student = student                       
                        obj.save()

                    generate_term_invoice_updated(
                        enrollment=enrollment,
                        term_registration=term_reg
                    )
                    messages.success(request, f"Term '{term}' registered successfully.")
                    return redirect('varsity_portal:enrollment_list')
    else:
        term_form = StudentTermRegistrationForm()
        formset = StudentSubjectEnrollmentFormSet()

    return render(request, 'varsity_portal/enrollment/term_registration_form.html', {
        'enrollment': enrollment,
        'term_form': term_form,
        'formset': formset,
        'subject_qs': subject_qs,
        'levels': levels,
        'terms': terms,
        'registered_term_ids': registered_term_ids, 
    })



@login_required
def get_terms_for_level(request):
    level_id = request.GET.get('level_id')
    enrollment_id = request.GET.get('enrollment_id')
    enrollment = get_object_or_404(VarsityStudentEnrollment, id=enrollment_id)

    terms = Term.objects.filter(level_id=level_id)
    data = [{'id': t.id, 'name': t.name} for t in terms]
    return JsonResponse({'terms': data})

@login_required
def get_subjects_for_term(request):
    term_id = request.GET.get('term_id')
    enrollment_id = request.GET.get('enrollment_id')
    enrollment = get_object_or_404(VarsityStudentEnrollment, id=enrollment_id)

    subjects = SubjectOffering.objects.filter(
        program=enrollment.program,
        term_id=term_id
    ).values('id', 'subject__name', 'subject__code')

    return JsonResponse({'subjects': list(subjects)})




@login_required
def student_term_registration_detail(request):
    student = Student.objects.filter(user=request.user).first()
    
    term_registrations = StudentTermRegistration.objects.filter(
        enrollment__student=student
    ).select_related(
        'enrollment', 'level'
    ).prefetch_related('courses__subject_offering__subject')

    print(f'student={student},term reg.={term_registrations}')

    return render(
        request,
        'varsity_portal/enrollment/term_registration_detail.html',
        {
            'student': student,
            'term_registrations': term_registrations
        }
    )




@login_required
def student_invoices_list(request):  
    student = None   
    student = get_object_or_404(Student, user=request.user)
    invoices = UniversityTermInvoice.objects.filter(student=student).order_by('-created_at')

    context = {
        'student': student,      
        'invoices': invoices,
    }
    return render(request, 'varsity_portal/invoices/student_invoice_list.html', context)


@login_required
def student_invoices_list(request):
    student = getattr(request.user, 'student_user', None)
    if not student:
        messages.warning(request,'logged in user is not student')
        return redirect('varsity_portal:enrollment_list')

    enrollment = student.varsity_student_enrollments.filter(is_active=True).first()
    if not enrollment:
        messages.warning(request,'logged in user is not student')
        return redirect('varsity_portal:enrollment_list')

    invoices = enrollment.varsity_student_term_invoices.order_by('-created_at')

    return render(request, 'varsity_portal/invoices/student_invoice_list.html', {
        'student': student,
        'enrollment': enrollment,
        'invoices': invoices,
    })



@login_required
def student_invoice_detail(request, invoice_id):
    invoice = get_object_or_404(UniversityTermInvoice, id=invoice_id, student__user=request.user)

    context = {
        'invoice': invoice,
    }
    return render(request, 'varsity_portal/invoices/student_invoice_details.html', context)


@login_required
def university_payment_list(request):   
    student = None     
    payments = UniversityPayment.objects.select_related('invoice', 'invoice__student').order_by('-paid_at')
    try:
        student = get_object_or_404(Student, user=request.user)
    except:
        messages.warning(request,'logged in user is not student')  
    payments=payments.filter(invoice__student=student)   
    return render(request, 'varsity_portal/payment/university_payment_list.html', {'payments': payments})




@login_required
def term_list(request):
    terms = Term.objects.all().order_by('name')
    return render(
        request,
        'varsity_portal/schedule/term_list.html',
        {'terms': terms}
    )


from collections import defaultdict
from university_management.models import ClassSchedule, Term

@login_required
def class_schedule_view(request, term_id):
    term = get_object_or_404(Term, id=term_id)   
    schedules_qs = ClassSchedule.objects.filter(term=term).order_by('day_of_week', 'start_time')
    schedules = defaultdict(list)
    for s in schedules_qs:
        day_name = s.get_day_of_week_display()
        schedules[day_name].append(s)
       
    schedules = dict(schedules)

    return render(request, 'varsity_portal/schedule/class_schedule_view.html', {
        'title': f"Class Schedule – {term.name}",
        'schedules': schedules,
        'term': term
    })



@login_required
def student_class_schedule(request, term_id):
    student=None
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.warning(request,'logged in user is not a student')
        return redirect('varsity_portal:enrollment_list')      
  
    term = get_object_or_404(Term, id=term_id)

    # Get schedules for the student in this term
    schedules_qs = ClassSchedule.objects.filter(
        term=term,
        subject_offering__student_subject_enrollment__student=student
    ).select_related(
        'subject_offering__subject',
        'teacher__user',
        'classroom'
    ).distinct().order_by('day_of_week', 'start_time')  # <--- add distinct()

    # Group by day
    schedules = defaultdict(list)
    for s in schedules_qs:
        day_name = s.get_day_of_week_display()
        schedules[day_name].append(s)
    schedules = dict(schedules)

    return render(request, 'varsity_portal/schedule/student_class_schedule_view.html', {
        'title': f"My Class Schedule – {term.name}",
        'schedules': schedules,
        'term': term,
        'student': student,
    })


from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def student_class_schedule_calendar(request, term_id):
    student=None
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.warning(request,'logged in user is not a student')
        return redirect('varsity_portal:enrollment_list')   
    
    term = get_object_or_404(Term, id=term_id)
  
    subject_offering_ids = student.subject_enrollments.filter(
        term_registration__term=term
    ).values_list('subject_offering_id', flat=True)
 
    schedules_qs = ClassSchedule.objects.filter(       
        subject_offering_id__in=subject_offering_ids
    ).select_related(
        'subject_offering__subject',
        'teacher',
        'classroom'
    ).order_by('day_of_week', 'start_time')

    DAYS = (
    (7, 'Sunday'),
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
    )
  
    time_slots = sorted({
        (s.start_time.strftime('%H:%M'), s.end_time.strftime('%H:%M'))
        for s in schedules_qs
    })

    calendar = []
    for start, end in time_slots:
        row = {'time': f"{start} – {end}", 'days': {day_num: [] for day_num, _ in DAYS}}
        for s in schedules_qs:
            if s.start_time.strftime('%H:%M') == start and s.end_time.strftime('%H:%M') == end:
                row['days'][s.day_of_week].append(s)
        calendar.append(row)

    context = {
        'title': f"My Class Schedule – {term.name}",
        'term': term,
        'days': DAYS,
        'calendar': calendar,
    }

    return render(
        request,
        'varsity_portal/schedule/student_class_schedule_calendar.html',
        context
    )


class ExamListView(ListView):
    model = Exam
    template_name = 'varsity_portal/exams/exam_list.html'
    context_object_name = 'exams'


class ExamDetailView(DetailView):
    model = Exam
    template_name = 'varsity_portal/exams/exam_detail.html'


@login_required
def register_for_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    student = get_object_or_404(Student,user=request.user)
    if not is_fee_cleared(student, exam.academic_session, exam.term):
        messages.error(request, "You cannot register for this exam. Your fees are not fully paid.")
        return redirect('varsity_portal:exam_list')
    
    registration, created = ExamRegistration.objects.get_or_create(
        student=student,
        exam=exam
    )

    if created:
        messages.success(request, "You are successfully registered for the exam.")       
    else:
        messages.info(request, "You are already registered for this exam.")
    return redirect('varsity_portal:generate_admit_card', registration_id=registration.id)




@login_required
def generate_admit_card(request, registration_id):
    student = get_object_or_404(Student,user = request.user)
    registration = get_object_or_404(ExamRegistration, id=registration_id)   
    enrollment = student.varsity_student_enrollments.first()
    exam = registration.exam
    schedules = ExamSchedule.objects.filter(
        exam=exam,
        subject_offering__program= enrollment.program
    ).order_by('exam_date', 'start_time')

    context = {
        'student': student,
        'exam': exam,
        'schedules': schedules,       
    }

    return render(request, 'varsity_portal/admit_card.html', context)





@login_required
def student_transcript2(request, session_id=None, term_id=None):  
    student = Student.objects.filter(user=request.user).first()
    student_enrollment = student.varsity_student_enrollments.first()
    student_term_registration = student_enrollment.term_enrolled_registrations.first()
    if not student_enrollment:
        messages.info(request, "There is no enrollment for this student")
        return redirect('varsity_portal:enrollment_list')

    if session_id:
        sessions = AcademicSession.objects.filter(id=session_id)
    else:
        sessions = AcademicSession.objects.filter(id=student_enrollment.academic_session.id)

    transcript_data = []

    for session in sessions:       
        if term_id:
            terms = Term.objects.filter(id=term_id)
        else:
            terms = Term.objects.filter(level=student_term_registration.level)

        session_info = {'session': session, 'terms': []}

        for term in terms:
            subject_results = StudentSubjectResult.objects.filter(
                student=student,
                academic_session=session,
                term=term,
                is_published=True
            ).order_by('subject_offering__subject__code')

            try:
                term_gpa = StudentTermResult.objects.get(
                    student=student,
                    academic_session=session,
                    term=term
                )
            except StudentTermResult.DoesNotExist:
                term_gpa = None
            
            if not subject_results.exists() and term_gpa is None:
                continue

            session_info['terms'].append({
                'term': term,
                'subject_results': subject_results,
                'term_gpa': term_gpa
            })
  
     
        try:
            cgpa = StudentCGPA.objects.get(student=student, academic_session=session)
        except StudentCGPA.DoesNotExist:
            cgpa = None

        session_info['cgpa'] = cgpa
        transcript_data.append(session_info)

    context = {
        'student': student,
        'transcript_data': transcript_data,
    }

    return render(request, 'varsity_portal/results/student_transcript.html', context)




@login_required
def student_transcript(request, session_id=None, term_id=None):
    student = Student.objects.filter(user=request.user).first()
    enrollment = student.varsity_student_enrollments.first()

    if not enrollment:
        messages.info(request, "No enrollment found for this student.")
        return redirect('university_management:enrollment_list')

    if session_id:
        sessions = AcademicSession.objects.filter(id=session_id)
    else:
        sessions = AcademicSession.objects.filter(id=enrollment.academic_session.id)

    transcript_data = []

    for session in sessions:
        if term_id:
            terms = Term.objects.filter(id=term_id)
        else:
            terms = Term.objects.filter(
                studentsubjectresult__student=student,
                studentsubjectresult__academic_session=session,
                studentsubjectresult__is_published=True
            ).distinct()

        session_info = {'session': session, 'terms': []}

        for term in terms:         
            subject_results = StudentSubjectResult.objects.filter(
                student=student,
                term=term,
                academic_session=session,
                is_published=True
            ).order_by('subject_offering__subject__code')

            if not subject_results.exists():              
                continue

            term_result = StudentTermResult.objects.filter(
                student=student,
                term=term,
                academic_session=session,
                is_published=True
            ).first()

            session_info['terms'].append({
                'term': term,
                'subject_results': subject_results,
                'term_gpa': term_result.gpa if term_result else None,
                'term_credits': term_result.total_credits if term_result else None
            })

        cgpa_record = StudentCGPA.objects.filter(
            student=student,
            academic_session=session
        ).first()
        session_info['cgpa'] = cgpa_record.cgpa if cgpa_record else None
        session_info['total_credits'] = cgpa_record.total_credits if cgpa_record else None
        transcript_data.append(session_info)

    context = {
        'student': student,
        'transcript_data': transcript_data,
    }
    return render(request, 'varsity_portal/results/student_transcript.html', context)

from teachers.models import Teacher
from university_management.models import SubjectAssignment
from datetime import date
from django.db.models import Sum
from school_management.models import School

@login_required
def common_dashboard(request):
    user = request.user
    teacher = Teacher.objects.filter(user=user).first()
    today = date.today()
    school= School.objects.first() 
    total_students = Student.objects.count()
    total_programs = Program.objects.count()
    total_active_sessions = AcademicSession.objects.filter(is_active=True).count()
    total_terms = Term.objects.count()
    
    total_revenue = UniversityTermInvoice.objects.aggregate(total_paid=Sum('total_paid'))['total_paid'] or 0
    total_due = UniversityTermInvoice.objects.aggregate(total_due=Sum('due_amount'))['total_due'] or 0

    teacher_subjects = []
    if user.role == 'teacher':
        teacher_subjects = SubjectAssignment.objects.all()

    quick_links = [
        {'title': 'Student Enrollment', 'url': '/students/enroll/'},
        {'title': 'Term Invoices', 'url': '/university_management/revenue_dashboard/'},
        {'title': 'Class Schedule', 'url': '/faculty/schedule/'},
        {'title': 'Messages', 'url': '/messages/inbox/'},
    ]

    context = {
        'total_students': total_students,
        'total_programs': total_programs,
        'total_active_sessions': total_active_sessions,
        'total_terms': total_terms,
        'total_revenue': total_revenue,
        'total_due': total_due,
        'teacher_subjects': teacher_subjects,
        'quick_links': quick_links,
        'school':school
    }

    return render(request, 'varsity_portal/common_dashboard.html', context)
