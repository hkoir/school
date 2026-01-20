from django.db import models
from core.models import Employee

from accounts.models import CustomUser



class Teacher(Employee):
    teacher_id = models.CharField(max_length=20, unique=True,null=True,blank=True)
    school = models.ForeignKey('school_management.School', on_delete=models.CASCADE, null=True, blank=True)
    teacher_type = models.CharField(max_length=100,choices={'school':'school','college':'college','university':'university'},null=True,blank=True)
    profile_picture = models.ImageField(upload_to='teacher_pictures/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
            if not self.teacher_id:  
                self.teacher_id = self.generate_teacher_id()
            super().save(*args, **kwargs)


    def generate_teacher_id(self):
        year = str(self.joining_date.year)[-2:]  # Last two digits of the year 
        school_code = self.school.code.upper()[-4:]
        

        existing_teachers = Teacher.objects.filter(
            joining_date__year=self.joining_date.year,
            school=self.school
        ).count() + 1
 
        teacher_id = f"T{year}{school_code}{existing_teachers:04d}"
        return teacher_id


    def __str__(self):
        return f"{self.first_name} {self.last_name}"





class TeacherSalary(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='teacher_user')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.teacher} - {self.amount} - {self.paid_date}"




