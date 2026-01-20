
from django.db import models


from school_management.models import School
from teachers.models import Teacher
from accounts.models import CustomUser
from school_management.models import AcademicClass

from django.utils.timezone import now
from clients.models import Client
from school_management.models import Subject,Section,AcademicClass
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


from django.db.models import Sum
from results.models import Grade
from payments.utils import get_due_till_today

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='student_user')
    student_id = models.CharField(max_length=20, unique=True,null=True,blank=True)  
    student_type = models.CharField(max_length=100,choices={'school':'school','college':'college','university':'university'},null=True,blank=True)
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='student_guardians')
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    blood_group =models.CharField(max_length=100,null=True,blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'),('others','Others')])   
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    date_enrolled = models.DateField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True)
    attendance_policy = models.ForeignKey('attendance.AttendancePolicy', on_delete=models.CASCADE, null=True, blank=True)
    digital_signature = models.ImageField(upload_to='student_signatue/',null=True,blank=True)
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

    def has_due(self):
        dues = get_due_till_today(self)
        for fee_type, data in dues.items():
            if data.get('net_due', 0) > 0:
                return True
        return False

        

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
    

    def get_exam_overall(self, exam):          
            results = self.student_results.filter(
                exam_type__exam=exam,
                grade_point__isnull=False
            )

            if not results.exists():
                return None 
            
            total_gp = sum(r.grade_point for r in results)
            subject_count = results.count()
            avg_gp = total_gp / subject_count
     
            overall_grade = Grade.objects.order_by('-grade_point').filter(
                grade_point__lte=avg_gp
            ).first()

            return {
                "grade_point": round(avg_gp, 2),
                "gpa": overall_grade.name if overall_grade else None
            }
   

from school_management.models import Shift,Gender,Language
from django.db import transaction

class StudentEnrollment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.CharField(max_length=20,null=True, blank=True)     
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrolled_students")
    roll_number = models.CharField(max_length=20, blank=True)
    feestructure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, null=True, blank=True, related_name='enrolled_fees')
    attendance_policy = models.ForeignKey(
        'attendance.AttendancePolicy',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="enrolled_policy"
    )     
    academic_class=models.ForeignKey(AcademicClass,on_delete=models.CASCADE,null=True,blank=True) 
   
    gender = models.ForeignKey(Gender,on_delete=models.CASCADE,null=True, blank=True)
    shift = models.ForeignKey(Shift,on_delete=models.CASCADE,null=True, blank=True)
    language = models.ForeignKey(Language,on_delete=models.CASCADE,null=True, blank=True)  
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True) 

    is_active = models.BooleanField(default=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('roll_number', 'academic_year', 'section')  # Ensure roll number is unique per section and academic year

    def __str__(self):
        return f"{self.student} - {self.academic_class.name} ({self.academic_year})"
        
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

  



############################# New addition #############################################

from school_management.models import AcademicClass
from results.models import Exam,ExamType
from payments.models import AdmissionFee

class TuitionFeeAssignment(models.Model):
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='student_tuition_assignments')
    student_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='tuition_assignments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AdmissionFeeAssignment(models.Model):
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='student_admission_assignments')
    student_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='admission_assignments')
    admission_fee = models.ForeignKey(AdmissionFee, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class ExamFee(models.Model):    
    academic_year = models.IntegerField()
    student_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name='exam_fees',null=True,blank=True)
    language_version = models.CharField(
        max_length=20,
        choices=[
            ('bangla', 'Bangla'),
            ('english', 'English'),
            ('arabic', 'Arabic'),
        ],
        null=True,
        blank=True
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('academic_year', 'student_class', 'language_version', 'exam')

    def __str__(self):
        return f"{self.exam.name} - {self.amount} ({self.student_class})"



class ExamFeeAssignment(models.Model):
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='student_examfee_assignments')
    exam_fee = models.ForeignKey(ExamFee, on_delete=models.CASCADE)
    start_date = models.DateField(null=True,blank=True,)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class TransportRoute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    pickup_point = models.CharField(max_length=255)
    drop_point = models.CharField(max_length=255)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.pickup_point} → {self.drop_point})"



class TransportAssignment(models.Model):
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='student_transport_assignments')
    student_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='transport_assignments',null=True,blank=True,)
    varsity_enrollment = models.ForeignKey(
        'university_management.VarsityStudentEnrollment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='varsity_transport_assignments'
    )
   
    route = models.ForeignKey(TransportRoute, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

   
    def __str__(self):
        return f"{self.student.name} (transport: {self.route})"




class RoomType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"



class Hostel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class HostelRoom(models.Model):    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='hostel_rooms')
    room_number = models.CharField(max_length=50)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='rooms_type')
    description = models.TextField(null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hostel', 'room_number') 

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number} ({self.room_type.name})"


class HostelAssignment(models.Model):
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='student_hostel_assignments')
    student_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='hostel_assignments')
    varsity_enrollment = models.ForeignKey(
        'university_management.VarsityStudentEnrollment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='varsity_hostel_assignments'
    )
    hostel_room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    def __str__(self):
        return f"{self.student.name} (room: {self.hostel_room})"




class OtherFee(models.Model):
    FEE_TYPE_CHOICES = [     
    
        ('id_card', 'ID Card Fee'),
        ('excursion', 'Excursion Fee'),  
        ('other', 'Other'),
    ]

    academic_year = models.IntegerField()
    student=models.ForeignKey('students.Student',on_delete=models.CASCADE,null=True,blank=True,related_name='other_fees_students')
    student_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='student_other_fees')
    fee_type = models.CharField(max_length=50, choices=FEE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.get_fee_type_display()} - {self.amount} ({self.student})"










