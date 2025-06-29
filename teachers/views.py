from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from.models import Teacher
from.forms import TeacherForm


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

