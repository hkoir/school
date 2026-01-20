from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from students.models import Student
from school_management.models import Subject, Schedule,ClassTeacher
from results.models import ExamType
from.models import Teacher
from.forms import TeacherForm



@login_required
def teacher_dashboard(request):
    teacher = Teacher.objects.filter(user=request.user).first()
    if not teacher:
        messages.warning(request, "No teacher record found. Contact admin.")
        return redirect('teachers:create_teacher')    
    academic_year = timezone.now().year

    class_assignments = teacher.assigned_class_teachers.filter(academic_year=academic_year)

    students = Student.objects.filter(
        enrolled_students__academic_class__in=[c.academic_class for c in class_assignments],
        enrolled_students__section__in=[c.section for c in class_assignments],
        enrolled_students__shift__in=[c.shift for c in class_assignments],
        enrolled_students__language__in=[c.language for c in class_assignments],
        enrolled_students__gender__in=[c.gender for c in class_assignments],
        enrolled_students__academic_year=academic_year
    ).distinct()
 
    subjects = Subject.objects.filter(
        schedules__subject_teacher=teacher,
        schedules__academic_year=academic_year
    ).distinct()
  
    today = timezone.now().date()
    schedule_today = Schedule.objects.filter(
        subject_teacher=teacher,
        academic_year=academic_year,
        date=today
    ).order_by('start_time')

    pending_exam_types = ExamType.objects.filter(
        academic_class__in=[c.academic_class for c in class_assignments],
        subject__in=subjects,
        exam__academic_year=academic_year,
        exam__is_exam_over=False
    ).select_related('exam', 'subject', 'academic_class').distinct()

    context = {
        'teacher': teacher,
        'classes': class_assignments,
        'students': students,
        'subjects': subjects,
        'schedule_today': schedule_today,
        'pending_exams': pending_exam_types,
    }
    return render(request, 'teachers/dashboard.html', context)




@login_required
def manage_teacher(request, id=None):  
    instance = get_object_or_404(Teacher, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = TeacherForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('teachers:create_teacher')  
    else:
        print(form.errors)

    datas = Teacher.objects.all().order_by('-name')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = TeacherForm(instance=instance)
    return render(request, 'teachers/manage_teacher.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_teacher(request, id):
    instance = get_object_or_404(Teacher, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('teachers:create_teacher')  

    messages.warning(request, "Invalid delete request!")
    return redirect('teachers:create_teacher') 




from.models import Teacher
from.forms import TeacherFilterForm


@login_required
def view_teacher_vcard(request):
    teacher_name = None
    teacher_records = Teacher.objects.all().order_by('-joining_date')

    form=TeacherFilterForm(request.GET or None)

    if form.is_valid():
        teacher_id = form.cleaned_data['teacher_id']
        if teacher_id:
            teacher_records=teacher_records.filter(teacher_id=teacher_id)

    paginator = Paginator(teacher_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    form=TeacherFilterForm()
    return render(request, 'teachers/view_teacher_vcard.html', 
    {
        'teacher_records': teacher_records,
        'form':form,
        'page_obj':page_obj
    })

