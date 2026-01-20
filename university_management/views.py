
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse,JsonResponse
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
import json
from collections import defaultdict
from django.db.models import Sum
from datetime import date
from django.contrib.auth.decorators import user_passes_test

from.utils import generate_term_invoice,generate_term_invoice_updated,is_fee_cleared,calculate_and_update_term_result

from students.models import Student
from .models import (   
    StudentSubjectResult,VarsityStudentEnrollment,
    StudentTermResult,SubjectOffering,
    StudentCGPA,ExamRegistration,
    AcademicSession,Exam, ExamSchedule,
    Term,UniversityTermInvoice,UniversityPayment,StudentTermRegistration,ClassSchedule,
    AcademicLevel,SubjectAssignment,Program,UniversityFeeStructure
)

from attendance.models import AttendancePolicy

from .forms import (
    StudentSubjectResultFormSet,UniversityPaymentForm,
    StudentTermRegistrationForm,StudentSubjectEnrollmentForm,StudentSubjectEnrollmentFormSet,
    ExamScheduleForm,StudentEnrollmentForm,ExamForm,ExamScheduleFormSet,ClassScheduleFormSet
)



class StudentEnrollmentCreateView(LoginRequiredMixin, CreateView):
    model = VarsityStudentEnrollment
    form_class = StudentEnrollmentForm
    template_name = 'university_management/enrollment/enrollment_form.html'
    success_url = reverse_lazy('university_management:enrollment_list')

    def form_valid(self, form):
        return super().form_valid(form)


@login_required
def student_enrollment(request):   
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
            enrollment.attendance_policy = attendance_policy           
            enrollment.save()

            return redirect('university_management:create_term_registration', enrollment.id)
    else:
        form = StudentEnrollmentForm()

    return render(
        request,
        'university_management/enrollment/enrollment_form.html',
        {'form': form}
    )


class StudentEnrollmentListView(LoginRequiredMixin, ListView):
    model = VarsityStudentEnrollment
    template_name = 'university_management/enrollment/enrollment_list.html'
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



@login_required
def term_registration_create(request, enrollment_id):
    levels= AcademicLevel.objects.all()
    terms = Term.objects.all()
    enrollment = get_object_or_404(VarsityStudentEnrollment, id=enrollment_id)
    student = enrollment.student

    subject_qs = SubjectOffering.objects.filter(
        subject__program=enrollment.program,        
    )

    registered_term_ids = StudentTermRegistration.objects.filter(
        enrollment=enrollment
    ).values_list('term_id', flat=True)

    if request.method == 'POST':
        term_form = StudentTermRegistrationForm(request.POST)
        formset = StudentSubjectEnrollmentFormSet(
            request.POST,
            subject_qs=subject_qs
        )

        if term_form.is_valid() and formset.is_valid():
            term = term_form.cleaned_data['term']

            if term.id in registered_term_ids:
                messages.error(request, f"Term '{term}' already registered.")
            else:
                with transaction.atomic():
                    term_reg = term_form.save(commit=False)
                    term_reg.enrollment = enrollment
                    term_reg.student = student                   
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

                messages.success(request, "Term registered successfully.")
                return redirect('university_management:enrollment_list')
        else:
            print(term_form.errors)
            print(formset.errors)

    else:
        term_form = StudentTermRegistrationForm()
        formset = StudentSubjectEnrollmentFormSet(
            subject_qs=subject_qs
        )

    return render(request, 'university_management/enrollment/term_registration_form.html', {
        'enrollment': enrollment,
        'term_form': term_form,
        'formset': formset,
        'levels':levels
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
def student_term_registration_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    term_registrations = StudentTermRegistration.objects.filter(
        enrollment__student=student
    ).select_related(
        'enrollment', 'level', 'term'
    ).prefetch_related('courses__subject_offering__subject')

    print(f'student={student},term reg.={term_registrations}')

    return render(
        request,
        'university_management/enrollment/term_registration_detail.html',
        {
            'student': student,
            'term_registrations': term_registrations
        }
    )



@login_required
def term_list(request):
    terms = Term.objects.all().order_by('name')
    return render(
        request,
        'university_management/schedule/term_list.html',
        {'terms': terms}
    )

@login_required
def class_schedule_create(request, term_id):
    term = get_object_or_404(Term, id=term_id)
    qs = ClassSchedule.objects.filter(subject_offering__term=term,subject_offering__term__level__program = term.level.program)
  
    subject_qs = SubjectOffering.objects.filter(term=term,subject__program = term.level.program)

    if request.method == 'POST':
        formset = ClassScheduleFormSet(
            request.POST,
            queryset=qs,
            form_kwargs={'subject_qs': subject_qs},
            subject_qs=subject_qs
        )

        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                for obj in instances:
                    obj.full_clean()
                    obj.save()
                for obj in formset.deleted_objects:
                    obj.delete()
            return redirect('university_management:class_schedule_view', term_id=term.id)

    else:
        formset = ClassScheduleFormSet(
            queryset=qs,
            form_kwargs={'subject_qs': subject_qs},
            subject_qs=subject_qs
        )

    return render(request, 'university_management/schedule/class_schedule_form.html', {
        'term': term,
        'formset': formset,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Prefetch
from django.utils import timezone



@login_required
def schedule_calendar_view(request, term_id):
    term = get_object_or_404(Term, id=term_id)

    # Detect user roles
    is_teacher = hasattr(request.user, 'teacher')
    is_student = hasattr(request.user, 'student')

    teacher = None
    student = None
    teacher_id = request.GET.get('teacher')
    student_id = request.GET.get('student')

    # Base queryset
    schedules_qs = ClassSchedule.objects.select_related(
        'teacher',
        'subject_offering__subject',
        'classroom',
    ).order_by('day_of_week', 'start_time')

    # CASE 1: Teacher viewing their own schedule
    if is_teacher and not (teacher_id or student_id):
        teacher = request.user.teacher
        schedules_qs = schedules_qs.filter(teacher=teacher, subject_offering__term=term)
        title = f"My Teaching Schedule – {term.name}"

    # CASE 2: Student viewing their own schedule
    elif is_student and not (teacher_id or student_id):
        student = request.user.student
        subject_offering_ids = student.subject_enrollments.filter(
            term_registration__term=term
        ).values_list('subject_offering_id', flat=True)

        schedules_qs = schedules_qs.filter(subject_offering_id__in=subject_offering_ids)
        title = f"My Class Schedule – {term.name}"

    # CASE 3: Admin/Staff viewing teacher schedule via dropdown
    elif teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        schedules_qs = schedules_qs.filter(teacher=teacher, subject_offering__term=term)
        title = f"{teacher.name}'s Teaching Schedule – {term.name}"

    # CASE 4: Admin/Staff viewing student schedule via dropdown
    elif student_id:
        student = get_object_or_404(Student, id=student_id)
        subject_offering_ids = student.subject_enrollments.filter(
            term_registration__term=term
        ).values_list('subject_offering_id', flat=True)

        schedules_qs = schedules_qs.filter(subject_offering_id__in=subject_offering_ids)
        title = f"{student.name}'s Class Schedule – {term.name}"

    else:
        messages.info(request, "Select Teacher or Student to view schedule.")
        schedules_qs = schedules_qs.none()
        title = f"Schedule Viewer – {term.name}"

    # Prepare calendar grid
    DAYS = (
        (7, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'),
        (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'),
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
   
    teachers = Teacher.objects.all().order_by('name')
    students = Student.objects.all().order_by('name')

    return render(
        request,
        'university_management/schedule/class_schedule_view.html',
        {
            'title': title,
            'term': term,
            'days': DAYS,
            'calendar': calendar,
            'teachers': teachers,
            'students': students,
            'teacher_id': teacher_id,
            'student_id': student_id,
            'is_teacher': is_teacher,
            'is_student': is_student,
        }
    )


from teachers.models import Teacher

@login_required
def teacher_class_schedule(request, term_id):  
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.warning(request, 'Logged in user is not a teacher')
        return redirect('university_management:common_dashboard')  
    term = get_object_or_404(Term, id=term_id)  
    schedules_qs = ClassSchedule.objects.filter(
        teacher=teacher,
        subject_offering__term=term
    ).select_related(
        'subject_offering__subject',
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
        'title': f"My Teaching Schedule – {term.name}",
        'term': term,
        'days': DAYS,
        'calendar': calendar,
    }

    return render(
        request,
        'university_management/schedule/teacher_class_schedule_view.html',
        context
    )


from django.contrib import messages

@login_required
def student_invoices_list(request):
    students=Student.objects.all()
    query = request.GET.get('q')
    enrollment = None
    invoices = UniversityTermInvoice.objects.none()

    if query:
        student=get_object_or_404(Student,student_id=query)
        enrollment = get_object_or_404(
            VarsityStudentEnrollment,
            student=student
        )
        invoices = enrollment.varsity_student_term_invoices.order_by('-created_at')

    return render(request, 'university_management/invoices/student_invoice_list.html', {
        'enrollment': enrollment,
        'student': enrollment.student if enrollment else None,
        'invoices': invoices,
        'students':students
    })



@login_required
def student_invoice_detail(request, invoice_id):
    students=Student.objects.all()
    query = request.GET.get('q')
    invoice = get_object_or_404(UniversityTermInvoice, id=invoice_id)
    if query:
        student=get_object_or_404(Student,student_id=query)       
        invoice = get_object_or_404(UniversityTermInvoice, id=invoice_id, student=student)
    context = {
        'invoice': invoice,
        'students':students
    }
    return render(request, 'university_management/invoices/student_invoice_details.html', context)



from decimal import Decimal
from .utils import create_student_fee_journal_entry


@login_required
def university_payment_create(request, invoice_id):
    invoice = get_object_or_404(UniversityTermInvoice, id=invoice_id)

    admission_due = invoice.admission_fee - (invoice.payments.aggregate(
        total=Sum('admission_paid')
    )['total'] or 0)

    tuition_due = invoice.tuition_fee - (invoice.payments.aggregate(
        total=Sum('tuition_paid')
    )['total'] or 0)

    if request.method == 'POST':
        form = UniversityPaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():

                payment = form.save(commit=False)
                payment.enrollment = invoice.enrollment
                payment.student = invoice.student
                payment.save()

                if payment.is_posted:
                    raise ValueError("Payment already posted")

                entry = create_student_fee_journal_entry(
                    payment_date=payment.paid_at or date.today(),
                    reference=f"PAY-{payment.id}",
                    student_name=payment.student.name,
                    tuition_amount=Decimal(str(payment.tuition_paid or 0)),
                    admission_amount=Decimal(str(payment.admission_paid or 0)),
                    tax_policy = payment.tax_policy,
                    created_by=request.user
                )

                payment.journal_entry = entry
                payment.is_posted = True
                payment.save(update_fields=['journal_entry','is_posted'])

            return redirect('university_management:payment_list')
    else:
        form = UniversityPaymentForm(initial={
            'invoice': invoice,
            'admission_paid': admission_due,
            'tuition_paid': tuition_due
        })

    return render(request, 'university_management/payment/university_payment_form.html', {
        'form': form,
        'invoice': invoice,
        'admission_due': admission_due,
        'tuition_due': tuition_due
    })


@login_required
def university_payment_list(request):
    query = request.GET.get('q')
    enrollment = None
    payments = UniversityPayment.objects.none()
    if query:
        enrollment = get_object_or_404(
            VarsityStudentEnrollment,
            student__student_id=query
        )
        payments = enrollment.varsity_student_term_payments.order_by('-paid_at')   
    students = Student.objects.all().order_by('name')  
    return render(request, 'university_management/payment/university_payment_list.html', {'payments': payments,'students':students})




class ExamListView(ListView):
    model = Exam
    template_name = 'university_management/exams/exam_list.html'
    context_object_name = 'exams'

def exam_list(request):
    exams=Exam.objects.all()
    students = Student.objects.all()
    return render(request,'university_management/exams/exam_list.html',{'exams':exams,'students':students})

class ExamCreateView(CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'university_management/exams/exam_form.html'
    success_url = reverse_lazy('university_management:exam_list')

class ExamUpdateView(UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'university_management/exams/exam_form.html'
    success_url = reverse_lazy('university_management:exam_list')

class ExamDetailView(DetailView):
    model = Exam
    template_name = 'university_management/exams/exam_detail.html'



class ExamDeleteView(DeleteView):
    model = Exam
    template_name = 'university_management/exams/exam_confirm_delete.html'
    success_url = reverse_lazy('university_management:exam_list')
    


class ExamScheduleCreateView(CreateView):
    model = ExamSchedule
    form_class = ExamScheduleForm
    template_name = 'university_management/exams/schedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam_id'] = self.kwargs['exam_id']  # Pass exam_id to template
        return context

    def form_valid(self, form):
        exam = Exam.objects.get(pk=self.kwargs['exam_id'])
        form.instance.exam = exam
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('university_management:exam_detail', kwargs={'pk': self.kwargs['exam_id']})


class ExamScheduleUpdateView(UpdateView):
    model = ExamSchedule
    form_class = ExamScheduleForm
    template_name = 'university_management/exams/schedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam_id'] = self.object.exam_id  
        return context

    def get_success_url(self):
        return reverse_lazy('university_management:exam_detail', kwargs={'pk': self.object.exam_id})

class ExamScheduleDeleteView(DeleteView):
    model = ExamSchedule
    template_name = 'university_management/exams/schedule_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('university_management:exam_detail', kwargs={'pk': self.object.exam.id})



def exam_create_with_schedule(request):
    if request.method == 'POST':
        exam_form = ExamForm(request.POST)
        schedule_formset = ExamScheduleFormSet(request.POST)     

       
        if exam_form.is_valid() and schedule_formset.is_valid():
            with transaction.atomic():
                exam = exam_form.save()
                schedules = schedule_formset.save(commit=False)
                for schedule in schedules:
                    schedule.exam = exam
                    schedule.save()
           
            return redirect('university_management:exam_detail', pk=exam.pk)      

    else:
        exam_form = ExamForm()
        schedule_formset = ExamScheduleFormSet()

    return render(request, 'university_management/exams/exam_schedule_form.html', {
        'exam_form': exam_form,
        'schedule_formset': schedule_formset,
    })

def exam_publish_toggle(request, pk):
    exam = get_object_or_404(Exam, pk=pk)

    if not exam.schedules.exists():
        messages.error(request, "Cannot publish exam without schedules.")
        return redirect('university_management:exam_detail', pk=pk)

    exam.is_published = True
    exam.save(update_fields=['is_published'])

    messages.success(request, "Exam published successfully.")
    return redirect('university_management:exam_detail', pk=pk)


@login_required
def register_for_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.all().order_by('name') 

    student = None
    registration = None
    message = None
    query = request.GET.get('q')
    if query:
        student = get_object_or_404(Student, student_id=query)       
        if not is_fee_cleared(student, exam.academic_session, exam.term):
            message = f"{student.name} cannot register. Fees not fully paid."
        else:           
            registration, created = ExamRegistration.objects.get_or_create(
                student=student,
                exam=exam
            )
            if created:
                message = f"{student.name} successfully registered for {exam.term}."
            else:
                message = f"{student.name} is already registered for {exam.term}."

    context = {
        'exam': exam,
        'students': students,
        'student': student,
        'registration': registration,
        'message': message,
    }

    return render(request, 'university_management/exams/register_for_exam.html', context)


@login_required
def generate_admit_card(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.all().order_by('name') 
   
    student = None
    registration = None
    schedules = []
    message = None
   
    query = request.GET.get('q')
    if query:
        student = get_object_or_404(Student, student_id=query)       
        registration = ExamRegistration.objects.filter(student=student, exam=exam).first()
        if registration:
            enrollment = student.varsity_student_enrollments.first()
            if enrollment:
                schedules = ExamSchedule.objects.filter(
                    exam=exam,
                    subject_offering__program=enrollment.program
                ).order_by('exam_date', 'start_time')
        else:
            message = f"{student.name} is not registered for this exam yet."

    context = {
        'exam': exam,
        'students': students,       
        'student': student,          
        'registration': registration,
        'schedules': schedules,
        'message': message,
    }

    return render(request, 'university_management/admit_card.html', context)
 
@login_required
def enter_student_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    query = request.GET.get('q')
    student = None
    students = Student.objects.all().order_by('name') 
    subject_qs = SubjectOffering.objects.none()
    formset = StudentSubjectResultFormSet(
        queryset=StudentSubjectResult.objects.none(),
        form_kwargs={'subject_qs': subject_qs}
    )

    if query:
        student = get_object_or_404(Student, student_id=query)     
        subject_qs = SubjectOffering.objects.filter(
            id__in=exam.schedules.values_list('subject_offering_id', flat=True),
            program=student.varsity_student_enrollments.first().program 
        )

        if request.method == 'POST':
            formset = StudentSubjectResultFormSet(
                request.POST,
                queryset=student.subject_results.filter(exam=exam),
                form_kwargs={'subject_qs': subject_qs}
            )
            if formset.is_valid():
                with transaction.atomic():
                    results = formset.save(commit=False)
                    for result in results:
                        result.student = student
                        result.exam = exam
                        result.term = exam.term
                        result.level = exam.term.level
                        result.academic_session = exam.academic_session
                        result.program = exam.program
                        result.academic_year = exam.academic_year
                        result.is_published = True
                        result.save()
                    for obj in formset.deleted_objects:
                        obj.delete()
                return redirect('university_management:student_transcript', student.id)
        else:
            formset = StudentSubjectResultFormSet(
                queryset=student.subject_results.filter(exam=exam),
                form_kwargs={'subject_qs': subject_qs}
            )

    return render(request, 'university_management/results/enter_subject_results.html', {
        'students': students,
        'student': student,
        'exam': exam,
        'formset': formset,
    })



@login_required
def student_transcript(request, student_id, session_id=None, term_id=None):
    student = get_object_or_404(Student, id=student_id)
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
    return render(request, 'university_management/results/student_transcript.html', context)



def is_top_management(user):   
    return user.is_authenticated and (user.role in ['admin', 'finance_manager', 'ceo'])

# @user_passes_test(is_top_management)
@login_required
def revenue_dashboard(request):
    if request.user.role not in ['admin', 'finance_manager', 'ceo','teacher','student']:
        messages.warning(request,'You are not authorized to view this report')
        return redirect('university_management:common_dashboard')
    
    selected_year = request.GET.get('academic_year')
    invoices = UniversityTermInvoice.objects.all()
    if selected_year:
        invoices = invoices.filter(academic_year=selected_year)

    academic_years = (
        UniversityTermInvoice.objects
        .values_list('academic_year', flat=True)
        .distinct()
        .order_by('-academic_year')
    )

    # Session-wise
    session_revenue = (
        invoices.values('academic_session__name')
        .annotate(
            total_paid=Sum('total_paid'),
            total_payable=Sum('total_payable'),
            total_due=Sum('due_amount')
        )
        .order_by('academic_session__name')
    )

    # Program-wise
    program_qs = (
        invoices.values('program__name')
        .annotate(total_revenue=Sum('total_paid'))
        .order_by('-total_revenue')
    )

    # Term-wise per program
    term_program_qs = (
        invoices.values('program__name', 'term__name')
        .annotate(total_revenue=Sum('total_paid'))
        .order_by('program__name', 'term__name')
    )

    # Prepare term-wise pie chart data
    term_program_map = defaultdict(dict)
    for row in term_program_qs:
        term_program_map[row['program__name']][row['term__name']] = float(row['total_revenue'] or 0)

    term_program_datasets = []
    for program, terms in term_program_map.items():
        term_program_datasets.append({
            'program': program,
            'labels': list(terms.keys()),
            'data': list(terms.values())
        })

    context = {
        'academic_years': academic_years,
        'selected_year': selected_year,
        'session_revenue': session_revenue,
        'program_revenue': program_qs,
        'term_program_datasets': term_program_datasets,

        # Pass JSON strings for JS
        'program_chart_json': json.dumps({
            'labels': [p['program__name'] for p in program_qs],
            'data': [float(p['total_revenue'] or 0) for p in program_qs]
        }),
        'term_program_json': json.dumps(term_program_datasets),
    }

    return render(request, 'university_management/report/revenue_dashboard.html', context)




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

    return render(request, 'university_management/report/common_dashboard.html', context)
