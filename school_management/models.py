from django.db import models

from teachers.models import Teacher
from .utils import DEPARTMENT_CHOICES,POSITION_CHOICES,GENDER_CHOICES,SHIFT_CHOICES,LANGUAGE_CHOICES

from accounts.models import CustomUser
from django.core.exceptions import ValidationError
from django.utils import timezone


class School(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=50,unique=True)   
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logo/',blank=True, null=True)
    contact_person = models.CharField(max_length=30,null=True,blank=True)
    phone = models.IntegerField(null=True,blank=True)
    email= models.EmailField(null=True,blank=True)
    state =models.CharField(max_length=20,null=True,blank=True)
    district = models.CharField(max_length=20,null=True,blank=True)
    city = models.CharField(max_length=30,null=True,blank=True)
    address = models.TextField()
    website = models.URLField(null=True, blank=True)
    date_of_establishment = models.DateField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    

class Department(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='school_user_department')   
    school = models.ForeignKey(School,on_delete=models.CASCADE,related_name='school_department')
    name = models.CharField(max_length=100,choices=DEPARTMENT_CHOICES)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name




class Position(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='school_user_position')
    school = models.ForeignKey(School,on_delete=models.CASCADE,related_name='school_positions')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="school_department_positions")
    name = models.CharField(max_length=100, choices=POSITION_CHOICES)      
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    



class Faculty(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    FACULTY_CHOICES = [
        ('arts', 'Arts'),
        ('commerce', 'Commerce'),
        ('science', 'Science'),
        ('general', 'General'),
    ]
    school = models.ForeignKey(School,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100, choices=FACULTY_CHOICES, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()



class AcademicClass(models.Model): 
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=50)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ClassAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True, blank=True)
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='assignments',null=True, blank=True)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, null=True, blank=True)
    language_version = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.academic_class.name}:Shift-{self.shift or ''} version-{self.language_version or ''} - {self.academic_year}"




class Section(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    class_assignment = models.ForeignKey(ClassAssignment, on_delete=models.CASCADE, related_name='sections',null=True, blank=True)
    name = models.CharField(max_length=20)  # A, B, C...
    class_gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    teacher_in_charge = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}-{self.class_gender or ''}"



class ClassRoom(models.Model):   
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100) 
    room_number = models.CharField(max_length=50, null=True, blank=True) 
    location = models.CharField(max_length=100, null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'room_number')  

    def __str__(self):
        return f"{self.name} - Room {self.room_number}"
    

class Subject(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='subjects',null=True, blank=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class SubjectAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty,on_delete=models.CASCADE,null=True,blank=True)
    academic_year = models.IntegerField(null=True, blank=True)
    class_assignment = models.ForeignKey(ClassAssignment, on_delete=models.CASCADE,null=True,blank=True ,related_name='student_subject_assignments') 
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    subject_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('class_assignment', 'section', 'subject', 'subject_teacher')  
    
    def __str__(self):
        return f"Class-{self.class_assignment}:section-{self.section}:Subject-{self.subject}"





class Schedule(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True,blank=True)
    day_of_week = models.CharField(max_length=20, choices=[
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ])
    subject_assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE, related_name='schedules',null=True, blank=True)
    shift = models.CharField(max_length=30, choices=SHIFT_CHOICES,null=True, blank=True)
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES,null=True, blank=True)
   
    date=models.DateField(null=True,blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):        
        if self.subject_assignment:
            conflicting_schedules = Schedule.objects.filter(
                subject_assignment=self.subject_assignment,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.id)

            for schedule in conflicting_schedules:
                if schedule.subject_assignment.subject == self.subject_assignment.subject:
                    raise ValidationError("Conflict: Another schedule exists for this subject in this section at this time.")
                
                if schedule.subject_assignment.subject_teacher == self.subject_assignment.subject_teacher:
                    raise ValidationError("Conflict: This teacher is already scheduled for another section or shift at this time.")
                
                if schedule.class_room == self.class_room:
                    raise ValidationError("Conflict: This classroom is already occupied at this time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_assignment.subject.name}--{self.subject_assignment.class_assignment.academic_class.name} {self.subject_assignment.section.name}--({self.start_time}--{self.end_time})"




class TeachingAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True, blank=True)
    class_assignment = models.ForeignKey(ClassAssignment, on_delete=models.CASCADE,null=True, blank=True)  # Class details
    section = models.ForeignKey(Section, on_delete=models.CASCADE)  # Section details
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        unique_together = ('class_assignment', 'section', 'teacher', 'classroom')

    def clean(self): 
        conflict = TeachingAssignment.objects.filter(
            class_assignment=self.class_assignment,
            section=self.section,
            teacher=self.teacher,
        ).exclude(id=self.id)
        
        if conflict.exists():
            raise ValidationError(f"{self.teacher.name} is already assigned to this class and section.")

    def __str__(self):
        return f"{self.class_assignment.academic_class.name} - {self.section.name} - {self.teacher.name} - {self.classroom.name}"


    
class ImageGallery(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField()
    CATEGORY_CHOICES = [
        ('background', 'Background Image'),
        ('event', 'Event Photo'),
        ('notice', 'Notice Board'),
        ('activity', 'School Activities'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="images")  
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    academic_class =models.ForeignKey(AcademicClass,on_delete=models.CASCADE,null=True,blank=True)   
    section = models.ForeignKey(Section,on_delete=models.CASCADE,null=True,blank=True)
    image = models.ImageField(upload_to='school_images/')    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.category}"
    
