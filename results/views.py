
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
from.models import Grade,Result,StudentFinalResult,ExamType,Exam
from.forms import ExamResultForm,GradeForm,ResultForm,ExamTypeForm
from django.db.models import Max, Subquery, OuterRef
from school_management.models import SubjectAssignment
from django.db.models import Case, When, Value, FloatField, F, Sum
from collections import Counter


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




def get_student_details(request):
    student_id = request.GET.get('student_id')
    print(f"Received student_id: {student_id}") 

    if not student_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    if not student_id.isdigit():
        return JsonResponse({'error': 'Invalid student_id format'}, status=400)
    try:
        student = Student.objects.get(id=student_id)
        first_enrollment = student.enrolled_students.first()     
        if first_enrollment:
            data = {
                'academic_year': first_enrollment.academic_year,              
                'subject_teacher':first_enrollment.student_class.student_subject_assignments.first().subject_teacher.id
                   }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'No enrollment found for this student'}, status=404)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)




from results.utils import calculate_and_create_final_result

@login_required
def manage_result(request, id=None):   
    instance = get_object_or_404(Result, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ResultForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = ResultForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False) 
            form_instance.user = request.user
            form_instance.save()
    
            student = form_instance.student
            subject = form_instance.exam_type.subject
            academic_year = form_instance.academic_year

            enrollment = student.enrolled_students.first()
            if enrollment:
                academic_class = enrollment.academic_class if enrollment.academic_class else None
                section = enrollment.section
                faculty = (
                    enrollment.academic_class.faculty
                    if enrollment.academic_class and enrollment.academic_class.faculty
                    else None
                )

            final_result = calculate_and_create_final_result(
            student=student,
            academic_year=academic_year,
            academic_class=academic_class,
            section=section,
            subject=subject,
            faculty=faculty
        )

        if final_result:
            form_instance.final_result = final_result
            form_instance.save()
            # form_instance.save(update_fields=['final_result'])
        elif not final_result:
                print("❌ Failed to calculate StudentFinalResult in view.")
        else:
            print("❌ No enrollment found.")

        messages.success(request, message_text)
        return redirect('results:create_result')  
    else:
        print(form.errors) 

    datas = Result.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'results/manage_result.html', {
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

    final_results = StudentFinalResult.objects.filter(
        student=student,
        academic_year=academic_year
    ).select_related('faculty', 'subject', 'academic_class', 'section', 'final_grade')

    total_grade_points = sum(result.final_grade.grade_point for result in final_results)
    total_subjects = final_results.count()
    gpa = round(total_grade_points / total_subjects, 2) if total_subjects > 0 else 0

   
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
        'gpa':final_grade_point,
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







def GPA_Final_result_analysis(request):
    form = ClassTopperReportFilterForm(request.GET or None)

    context = {
        'form': form,
        'grade_summary_data': None,
        'top_classes_gpa5': None,
        'top_classes_golden_gpa': None,
        'class_name': None,
        'section': None,
        'shift': None,
        'version': None,
        'class_gender': None,
        'academic_year': None,
        'students_with_golden_gpa': None,
        'top_students': None,
        'grade_point_labels': [],
        'grade_point_counts': [],
    }

    if request.method == 'GET' and form.is_valid():
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

        # GPA and percentage calculation per student
        students_with_percentage = results.values('student') \
            .annotate(
                total_obtained_marks_sum=Sum('total_obtained_marks'),
                total_assigned_marks_sum=Sum('total_assigned_marks')
            ).annotate(
                calculated_percentage=F('total_obtained_marks_sum') / F('total_assigned_marks_sum') * 100
            )

        students_with_all_gpa = students_with_percentage.annotate(
            calculated_gpa=Case(
                *[
                    When(calculated_percentage__gte=grade.min_marks,
                         calculated_percentage__lte=grade.max_marks,
                         then=Value(grade.grade_point))
                    for grade in Grade.objects.all()
                ],
                default=Value(0.0),
                output_field=FloatField()
            )
        )

        # Count GPA distribution
        grade_points = students_with_all_gpa.values_list('calculated_gpa', flat=True)
        grade_point_counts = Counter(grade_points)

        # --- Identify Golden GPA students (those who got 5.0 in all subjects)
        golden_student_ids = []
        for student_data in students_with_all_gpa:
            student_id = student_data['student']
            gpas = list(results.filter(student=student_id).values_list('grade_point', flat=True))
            if gpas and all(g == 5.0 for g in gpas):
                golden_student_ids.append(student_id)

        golden_gpa_count = len(golden_student_ids)
        grade_point_counts['Golden GPA'] = golden_gpa_count

        labels = list(grade_point_counts.keys())
        counts = list(grade_point_counts.values())

        # --- Golden GPA Student Data
        students_with_golden_gpa_data = Student.objects.filter(id__in=golden_student_ids).annotate(
            calculated_percentage=Subquery(
                students_with_all_gpa.filter(student=OuterRef('id')).values('calculated_percentage')[:1]
            )
        ).values(
            'name',
            'student_id',
            'enrolled_students__student_class__academic_class__name',
            'enrolled_students__section__name',
            'enrolled_students__student_class__shift',
            'enrolled_students__section__class_gender',
            'enrolled_students__student_class__language_version',
            'calculated_percentage'
        )

        # --- Top Scoring Students
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

        # --- Update context
        context.update({
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
    form = StudentTranscriptFilterForm(request.GET or None)

    if request.method == 'GET' and form.is_valid():
        student_id = form.cleaned_data.get('student_id')
        student = Student.objects.filter(student_id = student_id).first()
       
        if not Student.objects.filter(user=request.user).first():
            messages.warning(request,'you are not allowed to view this result')


        if student_id:
            student_results = Result.objects.filter(student__student_id=student_id).select_related('exam_type')
            final_result = StudentFinalResult.objects.filter(student__student_id=student_id).first()


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
        'total_assigned_marks': total_assigned_marks

    }

    return render(request, 'results/student_transcripts.html', context)



def generate_pdf(request,id=None):
    if id:       
        return generate_student_pdf(id)
    
    if request.method == "POST":
        student_id = request.POST.get('student_id')  
        if student_id:
            return generate_student_pdf(student_id)  

    return render(request, "results/student_id_form.html")  





def generate_student_pdf(student_id):
    student_with_golden_gpa_5 = False
    student = Student.objects.filter(student_id=student_id).first()
    if not student:
        return HttpResponse(f"Student with ID {student_id} not found.", status=404)

    student_results = Result.objects.filter(student__student_id=student_id).select_related('exam_type')
    if not student_results.exists():
        return HttpResponse(f"No results found for student with ID {student_id}.", status=404)

    final_results = StudentFinalResult.objects.filter(
        student__student_id=student_id
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
    response['Content-Disposition'] = f'attachment; filename="student_{student_id}_transcript.pdf"'

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
        result['student_name'] = student_object.name 
        result['student_class'] = student_object.enrolled_students.first().student_class

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
        'class_counts_values': json.dumps(class_counts_values)
    })
