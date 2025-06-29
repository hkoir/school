
from django.contrib.auth.decorators import login_required
from.models import  Notification
from django.contrib import messages
from students.models import Student
from.models import Message
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.http import require_POST


    
def create_notification(user, notification_type, message, student=None, teacher=None):
    if student:
        Notification.objects.create(student=student, message=message, notification_type=notification_type)
    elif teacher:
        Notification.objects.create(teacher=teacher, message=message, notification_type=notification_type)
    else:
        Notification.objects.create(user=user, message=message, notification_type=notification_type)




def mark_notification_as_read(notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()


