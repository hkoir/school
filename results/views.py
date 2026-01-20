


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, F, Case, When, ExpressionWrapper, FloatField, IntegerField,Count,Q,Max
import json


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Frame, PageTemplate
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
from django.conf import settings
from collections import defaultdict


from .models import Result, StudentFinalResult,Grade
from.forms import ClassTopperReportFilterForm,AggregateReportFilterForm,StudentTranscriptFilterForm
from students.models import Student
from school_management.models import Subject
from.models import Grade,Result,StudentFinalResult,ExamType
from.forms import ExamResultForm,GradeForm,ResultForm,ExamTypeForm
from django.db.models import Max, Subquery, OuterRef
from school_management.models import Subject
from django.db.models import Case, When, Value, FloatField, F, Sum
from collections import Counter









from students.models import StudentEnrollment,ExamFee,ExamFeeAssignment
from.forms import ExamCreationForm
from django.utils.timezone import now
from django.views.generic import ListView
from .models import Exam

def create_exam_with_fee(request,id=None):
    instance = get_object_or_404(Exam, id=id) if id else None
    if request.method == "POST":
        form = ExamCreationForm(request.POST)
        if form.is_valid():
            exam = form.save()
            
            exam_fee = ExamFee.objects.create(
                academic_year=exam.academic_year,
                student_class=form.cleaned_data['academic_class'],
                language_version=form.cleaned_data['language_version'],
                exam=exam,
                amount=form.cleaned_data['exam_fee_amount'],
                description=form.cleaned_data['description']
            )

            enrollments = StudentEnrollment.objects.filter(
                academic_year=exam.academic_year,
                academic_class=form.cleaned_data['academic_class'],
                language = form.cleaned_data['language_version']
                
            )

            count = 0
            for enrollment in enrollments:
                ExamFeeAssignment.objects.get_or_create(  # This will trigger Students.signals to create examfeepayment models
                    student=enrollment.student,
                    exam_fee=exam_fee,
                    defaults={'start_date': now().date()}
                )
                count += 1

            messages.success(
                request,
                f"Exam '{exam.name}' created successfully and assigned to {count} students!"
            )
            return redirect('results:exam_list')
    else:
        form = ExamCreationForm()
    return render(request, 'exams/create_exam_with_fee.html', {'form': form,'instance':instance})




class ExamListView(ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'


@login_required
def manage_grade(request, id=None):   
    instance = get_object_or_404(Grade, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = GradeForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = GradeForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('results:create_grade')  
        else:
            print(form.errors) 

    datas = Grade.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'results/manage_grade.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_grade(request, id):
    instance = get_object_or_404(Grade, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('results:create_grade')    

    messages.warning(request, "Invalid delete request!")
    return redirect('results:create_grade')  





def get_exam_types_for_exam(request):
    print("Entering into ajax...")
    exam_id = request.GET.get('exam_id')
    if exam_id:
        exam_types = ExamType.objects.filter(exam_id=exam_id)
        print(exam_types)  # Debugging the exam_types queryset
        data = [{'id': et.id, 'label': str(et)} for et in exam_types]
        return JsonResponse({'exam_types': data})
    else:
        return JsonResponse({'exam_types': []})



def get_exam_marks(request):
    exam_type_id = request.GET.get('exam_type_id')
    print(f"Received exam_type_id: {exam_type_id}") 

    if not exam_type_id:
        return JsonResponse({'error': 'exam_type_id is required'}, status=400)

  
    try:
        exam_type = ExamType.objects.get(id=exam_type_id)
      
        if  exam_type :
            data = {
                'exam_marks': exam_type.exam_marks,  
                'exam_date': exam_type.exam_date.strftime('%Y-%m-%d')       
            
                   }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'No enrollment found for this student'}, status=404)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)


from django.http import JsonResponse
from school_management.models import Schedule
def get_student_details(request):
    student_id = request.GET.get('student_id')

    if not student_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    if not student_id.isdigit():
        return JsonResponse({'error': 'Invalid student_id format'}, status=400)

    try:
        student = Student.objects.get(id=student_id)
        first_enrollment = student.enrolled_students.first()

        if not first_enrollment:
            return JsonResponse({'error': 'No enrollment found for this student'}, status=404)

        academic_year = first_enrollment.academic_year
        
        subject_teacher_qs = Schedule.objects.filter(
            academic_class=first_enrollment.academic_class,
            section=first_enrollment.section,
            shift=first_enrollment.shift,
            gender=first_enrollment.gender,
            language=first_enrollment.language
        )

        subject_teacher = list(subject_teacher_qs.values_list('id', flat=True))

        data = {
            'academic_year': str(academic_year),
            'subject_teacher': subject_teacher
        }

        return JsonResponse(data)

    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)



from results.utils import calculate_student_final_result

@login_required
def manage_result(request, id=None):
    instance = get_object_or_404(Result, id=id) if id else None
    form = ResultForm(request.POST or None, instance=instance)
    message_text = "updated successfully!" if id else "added successfully!"

    if request.method == "POST":
        if form.is_valid():
            result_instance = form.save(commit=False)
            result_instance.user = request.user
            result_instance.exam_type=form.cleaned_data['exam_type']
            result_instance.save()

            student = result_instance.student
            academic_year = result_instance.academic_year
            subject = result_instance.exam_type.subject

            # Get enrollment details for class/faculty/section
            enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
            academic_class = enrollment.academic_class if enrollment else None
            faculty = academic_class.faculty if academic_class else None
            section = enrollment.section if enrollment else None

            # Calculate final result for this single subject
            final_result = calculate_student_final_result(
                student=student,
                academic_year=academic_year,
                academic_class=academic_class,
                faculty=faculty,
                section=section,
                subject=subject
            )

            # Link this Result to its final_result
            if final_result:
                result_instance.final_result = final_result
                result_instance.save(update_fields=['final_result'])

            messages.success(request, message_text)
            return redirect('results:create_result')
        else:
            print("❌ Form errors:", form.errors)

    datas = Result.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "results/manage_result.html", {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })




@login_required
def delete_result(request, id):
    instance = get_object_or_404(Result, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('results:create_result')    

    messages.warning(request, "Invalid delete request!")
    return redirect('results:create_result')  





@login_required
def manage_exam_type(request, id=None):   
    instance = get_object_or_404(ExamType, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ExamTypeForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = ExamTypeForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False)            
            form_instance.user = request.user
            form_instance.save()              
            
            messages.success(request, message_text)
            return redirect('results:create_exam_type')  
        else:
            print(form.errors) 

    datas = ExamType.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'results/manage_exam_type.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })





@login_required
def delete_exam_type(request, id):
    instance = get_object_or_404(ExamType, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('results:create_exam_type')    

    messages.warning(request, "Invalid delete request!")
    return redirect('results:create_exam_type')     



@login_required
def mark_exam_over(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if exam.is_exam_over:
        messages.warning(request, f"{exam.name} is already marked as over.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    exam.is_exam_over = True
    exam.save()

    messages.success(request, f"{exam.name} has been marked as completed.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


####################### Result sheet preparation ########################################



from.utils import aggregate_student_data,calculate_gpa_and_grade



def individual_exam_result(request):
    form = ExamResultForm(request.GET or None)
    exam_results = None
    final_grade = None
    total_obtained_marks = 0
    total_assigned_marks = 0
    overall_percentage = 0
    overall_exam_date = None
    student = None
    exam_results = Result.objects.none()

    if form.is_valid():
        student_id = form.cleaned_data['student_id']
        academic_year = form.cleaned_data['academic_year']
       
        exam = form.cleaned_data['exam']

        student = get_object_or_404(Student, student_id=student_id)
        exam_results = Result.objects.all()

        if academic_year:
            exam_results = exam_results.filter(academic_year=academic_year)

        if student_id:
            exam_results = exam_results.filter(student=student)    

        if exam:
            exam_results = exam_results.filter(exam_type__exam=exam)       

        if exam_results.exists():
            overall_exam_date = exam_results.first().exam_date
            total_obtained_marks = sum(result.obtained_marks for result in exam_results)
            total_assigned_marks = sum(result.exam_marks for result in exam_results)
            overall_percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
            final_grade = Grade.objects.filter(min_marks__lte=overall_percentage, max_marks__gte=overall_percentage).first()

    return render(request, 'results/individual_exam_result.html', {
        'form': form,
        'exam_results': exam_results,
        'total_obtained_marks': total_obtained_marks,
        'total_assigned_marks': total_assigned_marks,
        'overall_percentage': overall_percentage,
        'final_grade': final_grade,
        'overall_exam_date': overall_exam_date,
        'student': student,
    })


def aggregated_final_result(request):
    student_id = request.POST.get('student_id')
    academic_year = request.POST.get('academic_year')

    if not student_id or not academic_year:
        return render(request, 'results/aggregated_final_result.html', {
            'message': 'Student ID or Academic Year is missing.'
        })

    try:     
        student = Student.objects.get(student_id=student_id)  
    except Student.DoesNotExist:
        return render(request, 'results/aggregated_final_result.html', {
            'message': 'Student not found.'
        })
    
    if student.enrolled_students.first(): 
        enrollment = student.enrolled_students.first()
        if enrollment.academic_class and enrollment.academic_class.faculty and enrollment.academic_class.faculty.school.logo:
            logo_url = enrollment.academic_class.faculty.school.logo.url
            school_name = enrollment.academic_class.faculty.school.name
            school_address = enrollment.academic_class.faculty.school.address
            school_website = enrollment.academic_class.faculty.school.website   

    final_results = StudentFinalResult.objects.filter(
        student=student,
        academic_year=academic_year
    ).select_related('faculty', 'subject', 'academic_class', 'section', 'final_grade')

    total_grade_points = sum(result.final_grade.grade_point for result in final_results)
    total_subjects = final_results.count()
    gpa = round(total_grade_points / total_subjects, 2) if total_subjects > 0 else 0

    overall_exam_date = final_results.first().created_at.date()
   
    if not final_results.exists():
        return render(request, 'results/aggregated_final_result.html', {
            'message': 'No results found for the given student and academic year.'
        })   

    total_obtained_marks = sum(result.total_obtained_marks for result in final_results)
    total_assigned_marks = sum(result.total_assigned_marks for result in final_results)
    overall_percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
    final_grade = Grade.objects.filter(min_marks__lte=overall_percentage, max_marks__gte=overall_percentage).first()
    final_grade_point = final_grade.grade_point

    return render(request, 'results/aggregated_final_result.html', {
        'student': student,
        'academic_year': academic_year,
        'final_results': final_results,
        'total_obtained_marks': total_obtained_marks,
        'total_assigned_marks': total_assigned_marks,
        'overall_percentage': overall_percentage,
        'overall_exam_date':overall_exam_date,
        'gpa':final_grade_point
    })





def student_details_report(request):
    student_id = request.POST.get('student_id')
    academic_year = request.POST.get('academic_year')
    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return render(request, 'results/student_details_report.html', {
            'message': 'Student not found.'
        })

    student_results = Result.objects.filter(
        student=student, academic_year=academic_year
    ).select_related('subject', 'exam_type')

    if not student_results.exists():
        return render(request, 'results/student_details_report.html', {'message': 'No results found.'})

    exam_types = ExamType.objects.all().order_by("id")
    subjects = {}

    for result in student_results:
        subject_name = result.subject.name
        exam_type_name = result.exam_type.name

        if subject_name not in subjects:
            subjects[subject_name] = {
                et.name: {"total": 0, "obtained": 0, "highest_obtained": 0} for et in exam_types
            }

        subjects[subject_name][exam_type_name]["total"] += result.exam_marks or 0
        subjects[subject_name][exam_type_name]["obtained"] += result.obtained_marks
        subjects[subject_name][exam_type_name]["highest_obtained"] = max(
        subjects[subject_name][exam_type_name]["highest_obtained"],
        result.obtained_marks or 0
            )

    subject_wise_results = []
    total_marks = 0
    total_obtained = 0
    highest_obtained_marks = 0
    all_gpa_five = True

    for subject_name, exams in subjects.items():
        subject = Subject.objects.get(name=subject_name) 
        subject_total_marks = 0
        subject_total_obtained = 0

        for exam in exams.values():
            subject_total_marks += exam["total"]
            subject_total_obtained += exam["obtained"]

        highest_marks = Result.objects.filter(
            subject=subject  
        ).values('student').annotate(
            total_obtained=Sum('obtained_marks')
        ).aggregate(Max('total_obtained'))['total_obtained__max'] or 0

        subject_gpa, subject_letter_grade = calculate_gpa_and_grade(
            subject_total_obtained, subject_total_marks
        )

        subject_wise_results.append({
            "subject": subject_name,
            "exam_data": exams,
            "final_total": subject_total_marks,
            "final_obtained": subject_total_obtained,
            "final_highest": highest_marks,
            "subject_gpa": subject_gpa,
            "subject_letter_grade": subject_letter_grade
        })

        total_marks += subject_total_marks
        total_obtained += subject_total_obtained
        highest_obtained_marks = max(highest_obtained_marks, highest_marks)

        if subject_gpa < 5.0:
            all_gpa_five = False
    golden_gpa = all_gpa_five

    #################################################################
    # Grand total data over the year for a student
    student_data = aggregate_student_data(
        student=student,
        academic_year=academic_year,
        academic_class=student.enrolled_students.first().academic_class,
        section=student.enrolled_students.first().section,
        language_type=student.enrolled_students.first().student_class.language_version
    )

    yearly_total = student_data['total_marks']
    yearly_obtained = student_data['total_obtained']
    year_highest = student_data['total_highest']
    yearly_gpa = student_data['overall_gpa']

    #################################################################

    return render(request, 'results/student_details_report.html', {
        'subjects': subject_wise_results,
        'exam_types': exam_types,
        'student': student,
        'academic_year': academic_year,      
        'total_marks': total_marks,
        'total_obtained': total_obtained,
        'highest_obtained_marks': highest_obtained_marks,        
        'yearly_total': yearly_total,
        'yearly_obtained': yearly_obtained,
        'year_highest': year_highest,
        'yearly_gpa': yearly_gpa,
        'golden_gpa':golden_gpa
    })






from django.db.models import Q, Sum, F, Case, When, Value, FloatField, Max, Subquery, OuterRef
from collections import Counter
from django.shortcuts import render
import json

def GPA_Final_result_analysis(request):
    form = ClassTopperReportFilterForm(request.GET or None)

    context = {
        'grade_summary_data': None,
        'top_classes_gpa5': None,
        'top_classes_golden_gpa': None,
        'form': form,
        'class_name': None,
        'section': None,
        'shift': None,
        'version': None,
        'class_gender': None,
        'academic_year': None,
        'students_with_golden_gpa': None,
        'top_students': None,
    }

    if request.method == 'GET' and form.is_valid():
        # Get filters
        class_name = form.cleaned_data.get("class_name")
        subject = form.cleaned_data.get("subject")
        section = form.cleaned_data.get("section")
        shift = form.cleaned_data.get("shift")
        version = form.cleaned_data.get("version")
        class_gender = form.cleaned_data.get("class_gender")
        academic_year = form.cleaned_data.get("academic_year")

        filters = Q()
        if academic_year:
            filters &= Q(academic_year=academic_year)
        if subject:
            filters &= Q(subject=subject)
        if class_name:
            filters &= Q(student__enrolled_students__academic_class=class_name)
        if section:
            filters &= Q(student__enrolled_students__section=section)
        if shift and shift not in [None, '', 'not-applicable']:
            filters &= Q(student__enrolled_students__student_class__shift=shift)
        if version and version not in [None, '', 'not-applicable']:
            filters &= Q(student__enrolled_students__student_class__language_version=version)
        if class_gender and class_gender not in [None, '', 'not-applicable']:
            filters &= Q(student__enrolled_students__section__class_gender=class_gender)

        results = StudentFinalResult.objects.filter(filters)

        # Annotate GPA and percentage
        students_with_percentage = results.values('student') \
            .annotate(
                total_obtained_marks_sum=Sum('total_obtained_marks'),
                total_assigned_marks_sum=Sum('total_assigned_marks')
            ) \
            .annotate(
                calculated_percentage=F('total_obtained_marks_sum') / F('total_assigned_marks_sum') * 100
            )

        students_with_all_gpa = students_with_percentage.annotate(
            calculated_gpa=Case(
                *[
                    When(
                        calculated_percentage__gte=grade.min_marks,
                        calculated_percentage__lte=grade.max_marks,
                        then=Value(grade.grade_point)
                    )
                    for grade in Grade.objects.all()
                ],
                default=Value(0.0),
                output_field=FloatField()
            )
        )

        # Count GPA occurrences and golden GPA
        grade_points = students_with_all_gpa.values_list('calculated_gpa', flat=True)
        grade_point_counts = Counter(grade_points)

        # Identify golden GPA students (all subjects GPA 5.0)
        golden_student_ids = []
        for student in students_with_all_gpa:
            sid = student['student']
            subject_gpas = results.filter(student_id=sid).values_list('grade_point', flat=True)
            if all(gp == 5.0 for gp in subject_gpas):
                golden_student_ids.append(sid)

        golden_gpa_count = len(golden_student_ids)
        grade_point_counts['Golden GPA'] = golden_gpa_count

        # Prepare labels and data
        labels = list(grade_point_counts.keys())
        counts = list(grade_point_counts.values())

        # Safely get golden GPA students' data
        students_with_golden_gpa_data = Student.objects.filter(id__in=golden_student_ids) \
            .annotate(
                calculated_percentage=Subquery(
                    students_with_all_gpa.filter(student=OuterRef('pk')).values('calculated_percentage')[:1]
                )
            ) \
            .values(
                'name',
                'student_id',
                'enrolled_students__student_class__academic_class__name',
                'enrolled_students__section__name',
                'enrolled_students__student_class__shift',
                'enrolled_students__section__class_gender',
                'enrolled_students__student_class__language_version',
                'calculated_percentage'
            )

        # Top scorers
        highest_percentage = students_with_all_gpa.aggregate(Max('calculated_percentage'))['calculated_percentage__max']
        top_students = students_with_all_gpa.filter(calculated_percentage=highest_percentage).values(
            'student__name',
            'student__student_id',
            'student__enrolled_students__student_class__academic_class__name',
            'student__enrolled_students__section__name',
            'student__enrolled_students__student_class__shift',
            'student__enrolled_students__section__class_gender',
            'student__enrolled_students__student_class__language_version',
            'calculated_percentage'
        )

        # Update context
        context.update({
            'form': form,
            'class_name': class_name,
            'section': section,
            'shift': shift,
            'version': version,
            'class_gender': class_gender,
            'academic_year': academic_year,
            'grade_point_labels': json.dumps(labels),
            'grade_point_counts': json.dumps(counts),
            'students_with_golden_gpa': students_with_golden_gpa_data,
            'top_students': top_students,
            
        })

    return render(request, 'results/top_students_report.html', context)






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
    logo_url=None
    school_name =None
    school_address =None
    school_website =None      
     
    form = StudentTranscriptFilterForm(request.GET or None)
    if request.method == 'GET' and form.is_valid():
        student_id = form.cleaned_data.get('student_id')
        student = Student.objects.filter(student_id = student_id).first()
       
        if not Student.objects.filter(user=request.user).first():
            messages.warning(request,'you are not allowed to view this result')


        if student_id:
            student_results = Result.objects.filter(student__student_id=student_id).select_related('exam_type')
            final_result = StudentFinalResult.objects.filter(student__student_id=student_id).first()

            if student.enrolled_students.first(): 
                enrollment = student.enrolled_students.first()
                if enrollment.academic_class and enrollment.academic_class.faculty and enrollment.academic_class.faculty.school.logo:
                    logo_url = enrollment.academic_class.faculty.school.logo.url
                    school_name = enrollment.academic_class.faculty.school.name
                    school_address = enrollment.academic_class.faculty.school.address
                    school_website = enrollment.academic_class.faculty.school.website   

            highest_marks_subquery = StudentFinalResult.objects.filter(
                academic_year=OuterRef('academic_year'),
                subject=OuterRef('subject')
            ).order_by().values('subject').annotate(
                highest_marks=Max('total_obtained_marks')
            ).values('highest_marks')


            final_results = StudentFinalResult.objects.filter(
                student__student_id=student_id
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
        'total_assigned_marks': total_assigned_marks,
        'logo_url':logo_url,
        'school_name' : school_name,
        'school_address':school_address,
        'school_website' :school_website

    }

    return render(request, 'results/student_transcripts.html', context)


@login_required
def generate_pdf(request, id=None):
    student = None

    if id:
        student = get_object_or_404(Student, id=id)
        return generate_student_pdf(student)
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        return generate_student_pdf(student)
    student = Student.objects.filter(user=request.user).first()
    if student:
        return generate_student_pdf(student)
    students = Student.objects.all()
    return render(request, "results/student_id_form.html", {'students': students})




def generate_student_pdf(student):   
    student_with_golden_gpa_5 = False    
   
    if not student:
        return HttpResponse(f"Student with ID {student} not found.", status=404)

    student_results = Result.objects.filter(student=student).select_related('exam_type')
    if not student_results.exists():
        return HttpResponse(f"No results found for student with ID {student}.", status=404)

    final_results = StudentFinalResult.objects.filter(
        student=student
    ).select_related('faculty', 'subject', 'academic_class', 'section', 'final_grade')

    all_5_0 = True
    for result in final_results:
        if result.final_grade.grade_point != 5.0:
            all_5_0 = False
            break

    student_with_golden_gpa_5 = all_5_0     

    total_grade_points = sum(result.final_grade.grade_point for result in final_results)
    total_subjects = final_results.count()
    average_grade_point = round(total_grade_points / total_subjects, 2) if total_subjects > 0 else 0

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
    response['Content-Disposition'] = f'attachment; filename="student_{student}_transcript.pdf"'

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
      
        if student.enrolled_students.first():  # Check if enrollment exists
            enrollment = student.enrolled_students.first()
            if enrollment.academic_class and enrollment.academic_class.faculty and enrollment.academic_class.faculty.school.logo:
                logo_path = os.path.join(settings.MEDIA_ROOT, enrollment.academic_class.faculty.school.logo.name)
                canvas.drawImage(logo_path, 40, 730, width=50, height=50)
            else:
                print("No logo found for the school or faculty details are missing.")
        else:
            print("No enrollment found for the student.")


        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(300, 770, student.enrolled_students.first().academic_class.faculty.school.name)

        canvas.setFont("Helvetica", 10)
        canvas.drawCentredString(300, 755, student.enrolled_students.first().academic_class.faculty.school.address)
        canvas.drawCentredString(300, 740, student.enrolled_students.first().academic_class.faculty.school.website)

        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(300, 725, f"School Code: {student.enrolled_students.first().academic_class.faculty.school.code}")

        canvas.line(40, 720, 560, 720)
        canvas.restoreState()

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='header_template', frames=frame, onPage=add_page_header)
    doc.addPageTemplates([template])

    elements.append(Spacer(1, 50))  
    if student.profile_picture:
        profile_picture_path = os.path.join(settings.MEDIA_ROOT, student.profile_picture.name)
        img = Image(profile_picture_path, width=40, height=40)
        img.hAlign = 'LEFT' 
        elements.append(img)
        elements.append(Spacer(1, 12)) 
    elements.append(Paragraph(f"<b>Student ID:</b> {student.student_id} || <b>Student Name:</b> {student.name}", style))
    elements.append(Paragraph(f"<b>Class:</b> {student.enrolled_students.first().academic_class} || <b>Section:</b> {student.enrolled_students.first().section.name}", style))
    elements.append(Paragraph(f"<b>Shift:</b> {student.enrolled_students.first().shift.name} || <b>Version:</b> {student.enrolled_students.first().language.name} || <b>Gender:</b> {student.enrolled_students.first().gender.name}", style))
    elements.append(Paragraph(f"<b>Class teacher ID:</b>{student.enrolled_students.first().academic_class.class_schedules.first().class_teacher.class_teacher.teacher_id}||<b>Name:</b> {student.enrolled_students.first().academic_class.class_schedules.first().class_teacher.class_teacher.name}", style))
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
                 exam_type=result.exam_type
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

        elements.append(Spacer(1, 12))
        if student_with_golden_gpa_5 :
            elements.append(Paragraph(f"Congratulations! You have achieved a <b>Golden GPA 5.0</b>", styles['Heading3']))
        else:
            elements.append(Paragraph(f"AvgGPA: <b>{average_gpa}||AvgGradePoint{average_grade_point}</b>", styles['Heading3']))

    doc.build(elements)
    return response






def school_toppers(request):
    academic_year=None
    school = None
    if request.method == 'GET':
         academic_year = request.GET.get('academic_year')  
   
    if not academic_year:
        return render(request, 'results/school_toppers.html', {
            'message': 'Academic Year is missing.',
        })
    
    student_results = StudentFinalResult.objects.filter(academic_year=academic_year) \
        .values('student', 'academic_class') \
        .annotate(
            total_obtained_marks=Sum('total_obtained_marks'),
            total_assigned_marks=Sum('total_assigned_marks')
        ).order_by('-total_obtained_marks')            
    
    for result in student_results:
        student = result['student']        
        student_object = Student.objects.get(id=student)  
        school = student_object.school
        result['student_name'] = student_object.name 
        result['student_class'] = student_object.enrolled_students.first().academic_class

        total_obtained_marks = result['total_obtained_marks']
        total_assigned_marks = result['total_assigned_marks']
        percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks > 0 else 0
        result['percentage'] = round(percentage, 2)    

    student_results = sorted(student_results, key=lambda x: x['percentage'], reverse=True)  # Sort by percentage
    top_students = student_results[:10]  

    class_counts = {}
    for result in top_students:
        academic_class = result['academic_class']               
        academic_class_name = StudentFinalResult.objects.filter(
            student=result['student'], academic_class=academic_class
        ).first().academic_class.name        
        class_counts[academic_class_name] = class_counts.get(academic_class_name, 0) + 1
   
    class_names = list(class_counts.keys())
    class_counts_values = list(class_counts.values())
   
    return render(request, 'results/school_toppers.html', {
        'academic_year': academic_year,
        'student_results': student_results,
        'top_students': top_students,
        'class_counts': class_counts, 
        'class_names': json.dumps(class_names),
        'class_counts_values': json.dumps(class_counts_values),
        'school':school
    })


from django.shortcuts import render
from django.db.models import Sum, Avg
from .models import StudentFinalResult
from school_management.models import AcademicClass, Section, Shift, Language, Gender,School

def student_ranking_view(request):
    year = request.GET.get('year')
    selected_class = request.GET.get('class')
    selected_section = request.GET.get('section')
    selected_shift = request.GET.get('shift')
    selected_gender = request.GET.get('gender')
    selected_language = request.GET.get('language')
    school = School.objects.first()
    academic_classes = AcademicClass.objects.all()

    sections = Section.objects.all()
    shifts = Shift.objects.all()
    genders = Gender.objects.all()
    languages = Language.objects.all()

    section=None
    shift=None
    gender=None
    language=None
    academic_class=None

    results = []
    ranked_results = []

    if year and selected_class:
        qs = StudentFinalResult.objects.filter(
            academic_year=year,
            academic_class_id=selected_class
        )
        academic_class = get_object_or_404(AcademicClass,id=selected_class)

        if selected_section:
            qs = qs.filter(student__enrolled_students__section_id=selected_section)
            section = get_object_or_404(Section,id=selected_section)
        if selected_shift:
            qs = qs.filter(student__enrolled_students__shift_id=selected_shift)
            shift = get_object_or_404(Shift,id=selected_shift)
        if selected_gender:
            qs = qs.filter(student__enrolled_students__gender_id=selected_gender)
            gender = get_object_or_404(Gender,id=selected_gender)
        if selected_language:
            qs = qs.filter(student__enrolled_students__language_id=selected_language)
            language = get_object_or_404(Language,id=selected_language)

        results = qs.values(
            'student',
            'student__name',
            'student__student_id',
            'academic_class__name',
            'student__enrolled_students__section__name',
            'student__enrolled_students__gender__name',
            'student__enrolled_students__shift__name',
            'student__enrolled_students__language__name'
        ).annotate(
            total_obtained=Sum('total_obtained_marks'),
            total_assigned=Sum('total_assigned_marks'),
            gpa=Avg('grade_point'),
        )

        # compute percentage
        for r in results:
            if r['total_assigned'] > 0:
                r['percentage'] = (r['total_obtained'] / r['total_assigned']) * 100
            else:
                r['percentage'] = 0

        # order by percentage & gpa
        results = sorted(results, key=lambda x: (-x['percentage'], -x['gpa']))

        # add ranking
        rank = 1
        for r in results:
            r['rank'] = rank
            ranked_results.append(r)
            rank += 1

    context = {
        'year': year,
        'academic_classes': academic_classes,
        'sections': sections,
        'shifts': shifts,
        'genders': genders,
        'languages': languages,
        'ranked_results': ranked_results,
        'school':school,
        'selected_section':section.name if section else None,
        'selected_shift':shift.name if shift else None,
        'selected_gender':gender.name if gender else None,
        'selected_language':language.name if language else None,
        'selected_class':academic_class.name if academic_class else None,
    }
    return render(request, 'results/student_ranking.html', context)
