from django.db import models
from students.models import Student,Guardian
from teachers.models import Teacher
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from django.contrib import messages
from accounts.models import CustomUser
from payment_gatway.utils import send_sms
from core.utils import POSITION_CHOICES
from clients.models import Client


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE, related_name='student_notifications')
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.CASCADE, related_name='teacher_notifications')
    notification_type=models.CharField(max_length=20,choices=[('attendance','Attendance'),('payment-due','Payment_due'),('notice','Notice'),('general','General')], null=True, blank=True)
    message = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  

    def __str__(self):
        if self.student:
            return f"Notification for {self.student.name}: {self.message}"
        elif self.teacher:
            return f"Notification for {self.teacher.name}: {self.message}"
        elif self.user:
            return f"Notification for {self.user.get_full_name() or self.user.username}: {self.message}"
        return f"Notification: {self.message}"

    def mark_as_read(self):
        self.is_read = True
        self.save()





class ManagementMessage(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100,choices=POSITION_CHOICES, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='tenant_photo/', null=True, blank=True)
    signature = models.ImageField(upload_to='tenant_signature/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message of {self.name} -- {self.position}"

    class Meta:       
        pass


class HeroSlider(models.Model):
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.TextField(blank=True)
    button_text = models.CharField(max_length=100, blank=True)
    button_link = models.URLField(blank=True)
    image = models.ImageField(upload_to='slider/')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding and self.order == 0:
            max_order = HeroSlider.objects.aggregate(models.Max('order'))['order__max'] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Slide {self.id}"









class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,null=True,blank=True,related_name='student_message')
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.CASCADE, related_name='teacher_messages')
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE,null=True,blank=True)
    
    message_content = models.TextField()
    message_type = models.CharField(max_length=50, choices=[
        ('Attendance', 'Attendance'),
        ('Result', 'Result'),
        ('Fee', 'Fee'),
        ('General', 'General'),
    ],null=True,blank=True)
    
    date_sent = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to {self.guardian.name} about {self.student.first_name} {self.student.last_name}"
        

    def send_sms(self):
        if self.guardian and self.guardian.phone_number:    
            student = self.student             
            tenant = student.user.tenant              
            phone_number = self.guardian.phone_number
            message = self.message_content

            try:
                response = send_sms(tenant, phone_number, message)               

                if response:
                    self.is_sent = True
                    self.save()
                return response
            except Exception as e:
                print(f"SMS send failed: {str(e)}")
                return None
        else:
            print("Guardian or phone number missing")
            return None
        


@receiver(post_save, sender=Message)
def send_sms_on_message_creation(sender, instance, created, **kwargs):
    if created and not instance.is_sent:
        instance.send_sms()



class Conversation(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True) 
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    last_updated = models.DateTimeField(auto_now=True)
    is_group = models.BooleanField(default=False)

    def __str__(self):
        if self.name:
            return self.name
        return f"Conversation: {', '.join([user.username for user in self.participants.all()])}"




class CommunicationMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages',null=True,blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages',null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField() 
    is_read = models.BooleanField(default=False)
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)
    video = models.FileField(upload_to='message_videos/', null=True, blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    def __str__(self):
        return f"{self.sender.username}: {self.body[:30]}"
    

    

class MessageReadStatus(models.Model):
    message = models.ForeignKey(CommunicationMessage, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')











#============================== Email and sms settings =========================================

class TenantSMSConfig(models.Model):
    tenant = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="tenant_sms_config")
    provider_name = models.CharField(max_length=100,blank=True, null=True) 
    api_key = models.CharField(max_length=255,blank=True, null=True)
    api_url = models.URLField(blank=True, null=True) 
    sender_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.provider_name} config for {self.tenant.name}"



class GlobalSMSConfig(models.Model):
    provider_name = models.CharField(max_length=100,blank=True, null=True)
    api_key = models.CharField(max_length=255,blank=True, null=True)
    api_url = models.URLField(blank=True, null=True)
    sender_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Global SMS config ({self.provider_name})"




class TenantEmailConfig(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='tenant_email_config')
    email_host = models.CharField(max_length=255, blank=True, null=True)
    email_port = models.IntegerField(blank=True, null=True)
    email_use_ssl = models.BooleanField(default=True)
    email_host_user = models.EmailField(blank=True, null=True)
    email_host_password = models.CharField(max_length=255, blank=True, null=True)
    default_from_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Email Config for {self.client.name}"

