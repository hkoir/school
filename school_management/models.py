



from django.db import models
from teachers.models import Teacher
from .utils import DEPARTMENT_CHOICES,POSITION_CHOICES,GENDER_CHOICES,SHIFT_CHOICES,LANGUAGE_CHOICES
from accounts.models import CustomUser
from django.core.exceptions import ValidationError
from django.utils import timezone




class InstitutionType(models.TextChoices):
    SCHOOL = "school", "School"
    COLLEGE = "college", "College"
    UNIVERSITY = "university", "University"
    POLYTECHNIC = "polytechnic", "Polytechnic"
    MADRASA = "madrasa", "Madrasa"
    TRAINING = "training", "Training Institute"
    MEDICAL = "medical", "Medical / Nursing"

class School(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=50,unique=True)   
    institution_type = models.CharField(max_length=50,choices=InstitutionType.choices,null=True,blank=True)
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
    

class Faculty(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    FACULTY_CHOICES = [
        ('arts', 'Arts'),
        ('commerce', 'Commerce'),
        ('science', 'Science'),
        ('general', 'General'),
    ]
    school = models.ForeignKey(School,on_delete=models.CASCADE,null=True,blank=True,related_name='school_faculty')
    name = models.CharField(max_length=100, choices=FACULTY_CHOICES, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

    

from payments.models import FeeStructure

class AcademicClass(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)      
    name = models.CharField(max_length=50)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.faculty.name}-{self.name} "

class Subject(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SubjectAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name="subjects",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("subject", "academic_class") 

    def __str__(self):
        return f"{self.subject.name} -> {self.academic_class.name}"



class Shift(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)    
    name = models.CharField(max_length=20)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Section {self.name}"
    
class Gender(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)    
    name = models.CharField(max_length=20)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Section {self.name}"
    
class Language(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)    
    name = models.CharField(max_length=20)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Section {self.name}"
    
class Section(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)    
    name = models.CharField(max_length=20)   
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Section {self.name}"

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
    

class ClassTeacher(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True,blank=True)
    academic_class=models.ForeignKey(AcademicClass,on_delete=models.CASCADE,related_name='class_teachers')    
    gender = models.ForeignKey(Gender,on_delete=models.CASCADE,null=True, blank=True)
    shift = models.ForeignKey(Shift,on_delete=models.CASCADE,null=True, blank=True)
    language = models.ForeignKey(Language,on_delete=models.CASCADE,null=True, blank=True)  
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    class_teacher=models.ForeignKey(Teacher,on_delete=models.CASCADE,related_name='assigned_class_teachers') 

    
    def __str__(self):
        return f"{self.academic_class.name}--{self.gender}--{self.shift}-{self.language}-{self.section.name}-{self.class_teacher.name})"


class Schedule(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True, blank=True)
    day_of_week = models.CharField(
        max_length=20,
        choices=[
            ('Sunday', 'Sunday'),
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
        ]
    )
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, null=True, blank=True,related_name='class_schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
   
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, null=True, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, null=True, blank=True)  
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)  
   
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True)
    class_teacher = models.ForeignKey(ClassTeacher, on_delete=models.CASCADE, null=True, blank=True)
    subject_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True,related_name='subject_assigned_teachers')
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            'academic_class', 
            'subject', 
            'gender', 
            'shift', 
            'language', 
            'class_room', 
            'subject_teacher', 
            'day_of_week',
            'start_time', 
            'end_time'
        )
        ordering = ['academic_class', 'day_of_week', 'start_time']

    def clean(self):
        if self.subject:
            conflicting_schedules = Schedule.objects.filter(
                subject=self.subject,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                academic_class=self.academic_class,
                shift=self.shift,
                gender=self.gender,
                language=self.language
            ).exclude(id=self.id)

            if conflicting_schedules.exists():
                raise ValidationError("Conflict: Another schedule exists for this subject in this class, shift, gender, language at this time.")
               
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.name} -- {self.academic_class.name} ({self.shift.name if self.shift else ''}) -- {self.gender.name if self.gender else ''} -- {self.start_time} to {self.end_time}"



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
