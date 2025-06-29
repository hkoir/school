from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from.forms import ImageGalleryForm,SchoolForm
from.forms import ClassRoomForm,SubjectForm,ScheduleForm,TeachingAssignmentForm,ImageGalleryForm

from.forms import FacultyForm,ClassForm,SectionForm,ClassAssignmentorm,SubjectAssignmentorm
from.models import Faculty,AcademicClass,Section,ClassAssignment,SubjectAssignment
from.models import ClassRoom,Subject,Schedule,TeachingAssignment,ImageGallery,School

from django.http import JsonResponse
from students.models import Student
from attendance.models import Attendance





@login_required
def manage_image_gallery(request, id=None):  
    instance = get_object_or_404(ImageGallery, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ImageGalleryForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_image_gallery')  
    else:
        print(form.errors)

    datas = ImageGallery.objects.all().order_by('-updated_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ImageGalleryForm(instance=instance)
    return render(request, 'school_management/manage_image_gallery.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_image_gallery(request, id):
    instance = get_object_or_404(ImageGallery, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_image_gallery')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_image_gallery')  



def image_list(request):
    images = ImageGallery.objects.all()  # Fetch all images
    return render(request, 'school_management/image_list.html', {'images': images})


@login_required
def manage_school(request, id=None):  
    instance = get_object_or_404(School, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = SchoolForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_school')  
    else:
        print(form.errors)

    datas = School.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = SchoolForm(instance=instance)
    return render(request, 'school_management/manage_school.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_school(request, id):
    instance = get_object_or_404(School, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_school')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_school') 




@login_required
def manage_faculty(request, id=None):  
    instance = get_object_or_404(Faculty, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =FacultyForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_faculty')  
    else:
        print(form.errors)

    datas = Faculty.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = FacultyForm(instance=instance)
    return render(request, 'school_management/manage_faculty.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_faculty(request, id):
    instance = get_object_or_404(Faculty, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_faculty') 

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_faculty') 






@login_required
def manage_class_assignment(request, id=None):  
    instance = get_object_or_404(ClassAssignment, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =ClassAssignmentorm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_class_assignment')  
    else:
        print(form.errors)

    datas = ClassAssignment.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ClassAssignmentorm(instance=instance)
    return render(request, 'school_management/manage_class_assignment.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })





@login_required
def manage_subject_assignment(request, id=None):  
    instance = get_object_or_404(SubjectAssignment, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =SubjectAssignmentorm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_subject_assignment')  
    else:
        print(form.errors)

    datas = SubjectAssignment.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = SubjectAssignmentorm(instance=instance)
    return render(request, 'school_management/manage_subject_assignment.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_subject_assignment(request, id):
    instance = get_object_or_404(SubjectAssignment, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_subject_assignment')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_subject_assignment')   









@login_required
def delete_class_assignment(request, id):
    instance = get_object_or_404(ClassAssignment, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_class_assignment')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_class_assignment')   










@login_required
def manage_class(request, id=None):  
    instance = get_object_or_404(AcademicClass, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ClassForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_class')  
    else:
        print(form.errors)

    datas = AcademicClass.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ClassForm(instance=instance)
    return render(request, 'school_management/manage_class.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_class(request, id):
    instance = get_object_or_404(AcademicClass, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_class')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_class') 





@login_required
def manage_section(request, id=None):  
    instance = get_object_or_404(Section, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = SectionForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_section')  
    else:
        print(form.errors)

    datas = Section.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = SectionForm(instance=instance)
    return render(request, 'school_management/manage_section.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_section(request, id):
    instance = get_object_or_404(Section, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_section')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_section')  



################################################

@login_required
def manage_class_room(request, id=None):  
    instance = get_object_or_404(ClassRoom, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ClassRoomForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_class_room')  
    else:
        print(form.errors)

    datas = ClassRoom.objects.all().order_by('name')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ClassRoomForm(instance=instance)
    return render(request, 'school_management/manage_class_room.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_class_room(request, id):
    instance = get_object_or_404(ClassRoom, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_class_room')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_class_room')  




@login_required
def manage_subject(request, id=None):  
    instance = get_object_or_404(Subject, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = SubjectForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_subject')  
    else:
        print(form.errors)

    datas = Subject.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = SubjectForm(instance=instance)
    return render(request, 'school_management/manage_subject.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_subject(request, id):
    instance = get_object_or_404(Subject, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_subject')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_subject')  




@login_required
def manage_schedule(request, id=None):  
    instance = get_object_or_404(Schedule, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ScheduleForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:create_schedule')  
    else:
        print(form.errors)

    datas = Schedule.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ScheduleForm(instance=instance)
    return render(request, 'school_management/manage_schedule.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_schedule(request, id):
    instance = get_object_or_404(Schedule, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_schedule')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:create_schedule')  





@login_required
def manage_teaching_assignment(request, id=None):  
    instance = get_object_or_404(TeachingAssignment, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = TeachingAssignmentForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('school_management:creatteaching_assignment')  
    else:
        print(form.errors)

    datas = TeachingAssignment.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = TeachingAssignmentForm(instance=instance)
    return render(request, 'school_management/manage_teaching_assignment.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_teaching_assignment(request, id):
    instance = get_object_or_404(TeachingAssignment, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('school_management:create_teaching_assignment')  

    messages.warning(request, "Invalid delete request!")
    return redirect('school_management:createteaching_assignment')  





def send_sms(phone_number, message):
    url = "https://bulksmsbd.net/api/smsapi"
    api_key = "YOUR_API_KEY"  # Replace with your actual API key
    sender_id = "YOUR_SENDER_ID"  # Provided by the SMS provider

    payload = {
        "api_key": api_key,
        "senderid": sender_id,
        "number": phone_number,  # Single phone number
        "message": message
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        return "SMS Sent Successfully"
    else:
        return f"Failed to send SMS: {response.text}"






def mark_attendance(request, student_id, status):
    student = get_object_or_404(Student, id=student_id)
    guardian_phone = student.guardian.phone_number  # Assuming Guardian has a phone_number field

    # Save attendance record
    attendance = Attendance.objects.create(student=student, status=status)

    # Send SMS if the student is absent
    if status == 'Absent':
        message = f"Dear Guardian, {student.name} was absent today. Please contact school."
        sms_response = send_sms(guardian_phone, message)

    return JsonResponse({"message": "Attendance marked successfully"})



def notify_guardian(student):
    guardian_number = student.guardian.phone_number  # Assume guardian has a phone field
    message = f"Dear Guardian, {student.name} was absent today. Please contact school."
    return send_sms(guardian_number, message)
