from django.db import models


from school_management.models import School
from teachers.models import Teacher
from accounts.models import CustomUser
from school_management.models import AcademicClass

from django.utils.timezone import now
from clients.models import Client
from school_management.models import Subject,Section,ClassAssignment
from payments.models import FeeStructure
from decimal import Decimal




class Guardian(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)   
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address=models.TextField(null=True,blank=True)
    profile_picture = models.ImageField(upload_to='guardian_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"



class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True)   
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='student_guardians')
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'),('others','Others')])   
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    date_enrolled = models.DateField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True)
    attendance_policy = models.ForeignKey('attendance.AttendancePolicy', on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.student_id})"


    def save(self, *args, **kwargs):
        if not self.date_enrolled:
            self.date_enrolled = now().date()  # Set current date if not provided
        
        if not self.student_id:
            self.student_id = self.generate_student_id()

        super().save(*args, **kwargs)

    def generate_student_id(self):
        if not self.date_enrolled:
            raise ValueError("Cannot generate student ID without a date_enrolled.")

        year = str(self.date_enrolled.year)[-2:]  # Last two digits of the year
        school_code = self.school.code.upper()  
        school_code_4 = str(school_code)[-4:]


        existing_students = Student.objects.filter(
            date_enrolled__year=self.date_enrolled.year,
            school=self.school
        ).count() + 1
 
        student_id = f"S{year}{school_code_4}{existing_students:06d}"

        return student_id
   

from school_management.models import SubjectAssignment

class StudentEnrollment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField(null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrolled_students")
    feestructure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, null=True, blank=True, related_name='enrolled_fees')
    academic_year = models.PositiveIntegerField()  # Example: 2024, 2025   
    academic_class=models.ForeignKey(AcademicClass,on_delete=models.CASCADE,null=True,blank=True)
    student_class = models.ForeignKey(ClassAssignment, on_delete=models.CASCADE, related_name="enrolled_classes", null=True, blank=True)
    roll_number = models.CharField(max_length=20)  # Roll numbers are unique per class, per year
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name="enrolled_sections")
    subjects = models.ManyToManyField(Subject, blank=True, related_name="enrolled_subjects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('roll_number', 'academic_year', 'section')  # Ensure roll number is unique per section and academic year

    def __str__(self):
        return f"{self.student} - {self.student_class.academic_class.name} ({self.academic_year})"
  


    def get_subject_assignments(self):
        return SubjectAssignment.objects.filter(
            section=self.section,
            subject__in=self.subjects.all(),
            academic_year=self.academic_year,
            class_assignment__academic_class=self.academic_class,
            class_assignment__shift=self.student_class.shift,
            class_assignment__language_type=self.student_class.language_version
        )

    def get_admission_fee_for_month(self, month):
        fees = self.feestructure.admissionfee_policy.admission_fees.all() 
        total_fee = Decimal(0.00)       
       
        for fee in fees:
            if fee and fee.due_date.month == month:
                total_fee += fee.amount         
        return total_fee 

    

    def get_total_due_for_month(self, month):
        if not self.feestructure:
            return Decimal(0.00)
        monthly_fee = self.feestructure.monthly_tuition_fee
        admission_fee_due = self.get_admission_fee_for_month(month)        

        return monthly_fee + admission_fee_due 

    def __str__(self):
        return f"{self.student.name} - {self.student_class if self.student_class else 'Custom Subjects'} ({self.academic_year})"
