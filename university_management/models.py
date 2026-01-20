from django.db import models
from accounts.models import CustomUser
import random,string
from datetime import date
from django.core.exceptions import ValidationError
from results.models import Grade
from decimal import Decimal


class AcademicSession(models.Model):
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=20)  # "2024–2025"
    code = models.CharField(
        max_length=7,
        unique=True,
        blank=True,null=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def generate_session_code(self):
        start_year = self.start_date.year % 100
        end_year = self.end_date.year % 100
        return f"{start_year:02d}-{end_year:02d}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            base_code = self.generate_session_code()
            code = base_code
            counter = 1

            while AcademicSession.objects.filter(
                institution=self.institution,
                code=code
            ).exists():
                code = f"{base_code}-{counter}"
                counter += 1

            self.code = code

        super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.name} "
    

class Faculty(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='varsity_faculty_user')   
    school = models.ForeignKey('school_management.School',on_delete=models.CASCADE,null=True,blank=True,related_name='varsity_faculty')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school', 'name')


    def __str__(self):
        return self.name

    
class Department(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name='varsity_user_department')
    faculty = models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True,blank=True,help_text="Parent faculty (if applicable)")
    name = models.CharField(max_length=100,help_text="e.g., Computer Science, Physics")
    description = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


import re

class Program(models.Model):
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE) 
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=150,
        help_text="BSc in CSE, HSC Science, SSC Science"
    )
    code = models.CharField(max_length=50,null=True,blank=True, unique=True,)

    duration_years = models.PositiveIntegerField(
        help_text="Total duration of the program in years"
    )

    total_credits = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Only applicable for credit-based programs"
    )



    def generate_program_code(self):
        words = re.findall(r'[A-Za-z]+', self.name)      
        skip_words = {'in', 'of', 'and', 'the', 'for'}
        words = [w.upper() for w in words if w.lower() not in skip_words]

        if len(words) >= 2:
            code = f"{words[0][:3]}-{''.join(w[0] for w in words[1:])}"
        else:
            code = words[0][:5]
        return code
    
    def save(self, *args, **kwargs):
        if not self.code:
            base_code = self.generate_program_code()
            code = base_code
            counter = 1

            while Program.objects.filter(code=code).exists():
                code = f"{base_code}-{counter}"
                counter += 1

            self.code = code

        super().save(*args, **kwargs)



    def __str__(self):
        return self.name
    

class AcademicLevel(models.Model):    
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Program this level belongs to" )

    level_number = models.PositiveIntegerField(
        help_text="Class number or year number",null=True,blank=True )
    title = models.CharField(
        max_length=50,
        help_text="Class 5 / Year 2" )
    
    class Meta:
        unique_together = ('institution', 'program', 'level_number')


    def __str__(self):
        return self.title
    


class Term(models.Model): 
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)
    level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=50,
        help_text="Semester 1, Final Term")
    order = models.PositiveIntegerField(
        help_text="Ordering within the level",null=True,blank=True)
    
    class Meta:
        unique_together = ('level', 'order')

    def save(self, *args, **kwargs):    
        if self.order is None:
            last_order = Term.objects.filter(level=self.level).aggregate(
                last_order=models.Max('order')
            )['last_order']
            
            self.order = 1 if last_order is None else last_order + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} - {self.level}"



class LanguageVersion(models.Model): 
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)
    code = models.CharField(max_length=20)   # bangla, english, arabic
    name = models.CharField(max_length=50)   # Bangla Version
    class Meta:
        unique_together = ('institution', 'code')

    def __str__(self):
        return self.name
    


class AdmissionFeePolicy(models.Model):   
    policy_code = models.CharField(max_length=100, null=True, blank=True)    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="varsity_fees_program_admission", null=True, blank=True)
    language = models.ForeignKey(LanguageVersion,on_delete=models.CASCADE)
    total_admission_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Policy= {self.policy_code} for {self.language}-{self.program}"

  

    class Meta:
        unique_together = ('program','language')

    def generate_policy_code(self):
        random_string = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        return f"{self.program.code}-{self.language.name.upper()}-{random_string}"

    
    def save(self, *args, **kwargs):
        if not self.policy_code:
            self.policy_code = self.generate_policy_code()          
        super().save(*args, **kwargs)



class AdmissionFee(models.Model):  
    FEE_CHOICES = [
        ('registration', 'Registration'), 
        ('tuition', 'Tuition'), 
        ('sports', 'Sports'), 
        ('lab', 'Lab Fees'), 
        ('library', 'Library')
    ]

    admission_fee_policy = models.ForeignKey(AdmissionFeePolicy,on_delete=models.CASCADE,null=True,blank=True,related_name='varsity_admission_fees')
    fee_type = models.CharField(max_length=50,choices=FEE_CHOICES,null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_month = models.IntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)], null=True, blank=True)
    due_terms = models.ForeignKey(Term,on_delete=models.CASCADE,null=True,blank=True)
    due_date = models.DateField(null=True, blank=True)   
  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('admission_fee_policy', 'fee_type')

    def __str__(self):
        return f"Admission Fee for {self.fee_type}"
    


class UniversityFeeStructure(models.Model):   
    program = models.ForeignKey(Program,on_delete=models.CASCADE)   
    language = models.ForeignKey(LanguageVersion,on_delete=models.CASCADE)  
    per_credit_fee = models.DecimalField(max_digits=10,decimal_places=2)
    admission_fee = models.ForeignKey(AdmissionFeePolicy,on_delete=models.CASCADE,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fee for {self.language.name}--{self.program.code}-Charge per credit:{self.per_credit_fee}"

    

class Subject(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='varsity_subject_user')
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE,related_name="subjects",
        help_text="Institution this subject belongs to")
    faculty = models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True,blank=True,
        help_text="Faculty responsible for this subject (optional for schools)")
    department = models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True,
        help_text="Department offering this subject (mainly universities)")    
    program = models.ForeignKey(Program,on_delete=models.SET_NULL,null=True,blank=True,
        help_text="B.SC.M.Sc, Diploma etc")   
    code = models.CharField(max_length=20,help_text="Subject code (e.g., MAT101, PHY-9)")
    name = models.CharField(max_length=255)
    description = models.TextField(null=True,blank=True,
        help_text="Optional syllabus summary")

    is_credit_based = models.BooleanField(default=False,help_text="True for university credit subjects")
    total_credit = models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True,
        help_text="Default credit value (e.g., 3.00)")

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive subjects cannot be assigned"
    )
    per_credit_fee_override = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('institution', 'code')

    def __str__(self):
        return f"{self.program}--{self.name}--{self.code} "
    


class ClassRoom(models.Model):   
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,related_name='varsity_class_room_user')
    name = models.CharField(max_length=100) 
    room_number = models.CharField(max_length=50, null=True, blank=True)  
    building_name = models.CharField(max_length=100, null=True, blank=True)  
    floor=models.CharField(max_length=10)
    location = models.TextField(null=True, blank=True)   
    capacity = models.IntegerField(null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'room_number')  

    def __str__(self):
        return f"{self.building_name}--{self.name} - {self.room_number}"

    
class SubjectOffering(models.Model):
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)  
    program=models.ForeignKey(Program,on_delete=models.CASCADE,related_name='subjectoffering_program',null=True,blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)  
    level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)   
    term = models.ForeignKey(Term,null=True,blank=True,on_delete=models.SET_NULL)  
    max_students = models.PositiveIntegerField(default=50,help_text="Maximum students allowed in this subject offering")
    is_compulsory = models.BooleanField(default=True)
 

    class Meta:
        unique_together = (
            'subject','level', 'term')

    def __str__(self):
        return f"{self.subject.program}-{self.subject}-{self.level}-{self.term}"
    
    def seats_left(self):
        enrolled = self.studentsubjectenrollment_set.count()
        return max(self.max_students - enrolled, 0)

    def is_full(self):
        return self.seats_left() == 0
    
    def clean(self):
        current_count = StudentSubjectEnrollment.objects.filter(
            subject_offering=self.id,            
        ).count()

        if current_count >= self.max_students:
            raise ValidationError(
                f"{self.subject.name} "
                f"({self.program}) is already full."
            )


from django.db import transaction

class VarsityStudentEnrollment(models.Model):
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name="varsity_student_enrollments")
    academic_session = models.ForeignKey(AcademicSession,on_delete=models.CASCADE)    
    language = models.ForeignKey(LanguageVersion,on_delete=models.SET_NULL,null=True,blank=True)
    program = models.ForeignKey(Program,on_delete=models.SET_NULL,null=True,blank=True)     
    roll_number = models.CharField(max_length=20,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    fee_structure = models.ForeignKey(UniversityFeeStructure,on_delete=models.SET_NULL,null=True,blank=True)
    attendance_policy = models.ForeignKey('attendance.AttendancePolicy',on_delete=models.SET_NULL,null=True,blank=True,related_name='attendance_policy_varsity')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = (
            'student',
            'academic_session',
            'program'
        )


    def generate_roll_number(self):
        session_code = self.academic_session.code    # e.g. 25-29
        program_code = self.program.code               # e.g. BSEE

        last_enrollment = (
            VarsityStudentEnrollment.objects
            .filter(
                academic_session=self.academic_session,
                program=self.program
            )
            .order_by('-id')
            .first()
        )

        last_serial = 0
        if last_enrollment and last_enrollment.roll_number:
            try:
                last_serial = int(last_enrollment.roll_number.split('-')[-1])
            except ValueError:
                last_serial = 0

        new_serial = last_serial + 1
        return f"{session_code}-{program_code}-{str(new_serial).zfill(4)}"
    
    def save(self, *args, **kwargs):
        if not self.roll_number:
            with transaction.atomic():
                self.roll_number = self.generate_roll_number()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.student} - {self.program}"
    


    
class StudentTermRegistration(models.Model):
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    enrollment = models.ForeignKey(
        VarsityStudentEnrollment,
        on_delete=models.CASCADE,
        related_name='term_enrolled_registrations'
    )
    level = models.ForeignKey(AcademicLevel,on_delete=models.CASCADE)   
    term = models.ForeignKey(Term, on_delete=models.CASCADE,related_name='term_registrations')  
    is_fee_cleared = models.BooleanField(default=False)
    is_exam_eligible = models.BooleanField(default=False)
    is_registered = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment', 'term','level')

    def __str__(self):
        return f"{self.enrollment.student} - {self.term}-{self.enrollment.program}"


class StudentSubjectEnrollment(models.Model):   
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name='subject_enrollments')
    term_registration = models.ForeignKey(
        StudentTermRegistration,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    subject_offering = models.ForeignKey(SubjectOffering,on_delete=models.CASCADE,related_name='student_subject_enrollment')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'student',
            'subject_offering',           
            'term_registration'
        )

    def __str__(self):
        return f"{self.student} - {self.subject_offering.subject}"
    
   

class Exam(models.Model):
    institution = models.ForeignKey('school_management.School', on_delete=models.CASCADE)
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('improvement', 'Improvement'),
    ]
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('academic_session', 'program', 'level', 'term', 'exam_type')

    def __str__(self):
        return f"{self.program} - {self.term} - {self.exam_type}"



class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE)   
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.ForeignKey(ClassRoom,on_delete=models.CASCADE, null=True, blank=True,related_name='varsity_exam_venue')
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    class Meta:
        unique_together = ('exam', 'subject_offering')

    def __str__(self):
        return f"{self.exam} - {self.subject_offering.subject}"


class ExamRegistration(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE,related_name='exam_registrations')
    is_fee_cleared = models.BooleanField(default=False)
    admin_override = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student} - {self.exam}"
    


class AdmitCard(models.Model):
    registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to='admit_cards/', null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_printed = models.BooleanField(default=False)

    def __str__(self):
        return f"AdmitCard - {self.registration.student}"


class StudentSubjectResult(models.Model):
    academic_session = models.ForeignKey(AcademicSession,on_delete=models.CASCADE)
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name='subject_results')
    subject_offering = models.ForeignKey(SubjectOffering,on_delete=models.CASCADE)
    program = models.ForeignKey(Program,on_delete=models.CASCADE)   
    term = models.ForeignKey(Term,on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam,on_delete=models.CASCADE,null=True,blank=True,related_name='exam_subject_results')
    marks_obtained = models.DecimalField(max_digits=5,decimal_places=2)
    grade = models.CharField(max_length=10)
    grade_point = models.DecimalField(max_digits=3,decimal_places=2)
    credit = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    weighted_points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_absent = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'subject_offering', 'term','academic_session')


    def save(self, *args, **kwargs):
        if not self.is_absent:
            grade_obj = Grade.objects.filter(
                min_marks__lte=self.marks_obtained,
                max_marks__gte=self.marks_obtained
            ).first()

            if grade_obj:
                self.grade = grade_obj.name
                self.grade_point = Decimal(grade_obj.grade_point)
            else:
                self.grade = 'F'
                self.grade_point = Decimal('0.00')
        else:
            self.grade = 'F'
            self.grade_point = Decimal('0.00')
       
        self.credit = Decimal(self.subject_offering.subject.total_credit or 0)
        self.weighted_points = self.grade_point * self.credit

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student}-{self.program}-{self.term}-{self.subject_offering.subject}"
    


class StudentTermResult(models.Model):
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    academic_session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE
    )
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE
    )
    level = models.ForeignKey(
        AcademicLevel,
        on_delete=models.CASCADE
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE
    )

    total_credits = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2
    )

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'student',
            'academic_session',
            'term'
        )

    def __str__(self):
        return f"{self.program}-{self.student} - {self.term} GPA: {self.gpa}"
    


class StudentCGPA(models.Model):
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name='cgpa_records')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    total_credits = models.DecimalField(max_digits=7,decimal_places=2)
    cgpa = models.DecimalField(max_digits=4,decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'academic_session')

    def __str__(self):
        return f"{self.student} CGPA: {self.cgpa}"





class UniversityTermInvoice(models.Model):
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name='student_term_invoices')
    enrollment = models.ForeignKey(VarsityStudentEnrollment,on_delete=models.CASCADE,related_name='varsity_student_term_invoices',null=True,blank=True)
    academic_session = models.ForeignKey(AcademicSession,on_delete=models.CASCADE)
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    program = models.ForeignKey(Program,on_delete=models.CASCADE)
    level = models.ForeignKey(AcademicLevel,on_delete=models.CASCADE)
    term = models.ForeignKey(Term,on_delete=models.CASCADE)
    total_subjects = models.PositiveIntegerField()
    total_credits = models.DecimalField(max_digits=6, decimal_places=2)
    per_credit_fee = models.DecimalField(max_digits=10, decimal_places=2)
    tuition_fee = models.DecimalField(max_digits=10,decimal_places=2)
    admission_fee = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    total_payable = models.DecimalField(max_digits=10,decimal_places=2)
    total_paid = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
        ],
        default='unpaid'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'student',
            'academic_session',
            'term'
        )

    def __str__(self):
        return f"Invoice {self.student} - {self.term}"


class UniversityPayment(models.Model):
    student = models.ForeignKey('students.Student',on_delete=models.CASCADE,related_name='student_term_payment',null=True,blank=True)
    enrollment = models.ForeignKey(VarsityStudentEnrollment,on_delete=models.CASCADE,related_name='varsity_student_term_payments',null=True,blank=True)
    invoice = models.ForeignKey(UniversityTermInvoice,on_delete=models.CASCADE,related_name='payments')
    tax_policy = models.ForeignKey('core.TaxPolicy',on_delete=models.CASCADE,null=True,blank=True,related_name='varsity_tax_policies')
    amount_paid = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    tuition_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,null=True,blank=True
    )
    admission_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,null=True,blank=True
    )
    payment_method = models.CharField(max_length=20,choices=[
            ('cash', 'Cash'),
            ('bank', 'Bank Transfer'),
            ('bkash', 'bKash'),
            ('nagad', 'Nagad'),
            ('card', 'Card'),
        ]
    )
    transaction_id = models.CharField(max_length=100,null=True,blank=True)
    journal_entry = models.ForeignKey('accounting.JournalEntry',on_delete=models.CASCADE,related_name='varsity_payment_journal_entry',null=True,blank=True)
    is_posted = models.BooleanField(default=False,null=True,blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)

      
    @property
    def total_paid(self):
        return self.tuition_paid + self.admission_paid

    def __str__(self):
        return f"paid for {self.invoice}"




class SubjectAssignment(models.Model):
    academic_session=models.ForeignKey(AcademicSession,on_delete=models.CASCADE)
    academic_year =models.CharField(max_length=10,null=True,blank=True)
    subject_offering = models.ForeignKey(SubjectOffering,on_delete=models.CASCADE,related_name='varsity_teaching_assignments')
    subject_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True,related_name='varsity_subjetc_assignemnt')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'subject_offering',          
            'subject_teacher' )

    def __str__(self):
        return f"{self.subject_offering} - {self.subject_teacher}"

DAYS_OF_WEEK = (
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
    (7, 'Sunday'),
)

from .models import ClassRoom

class ClassSchedule(models.Model):
    session=models.ForeignKey(AcademicSession,on_delete=models.CASCADE,null=True,blank=True)
    academic_year =models.CharField(max_length=10,null=True,blank=True)   
    subject_offering = models.ForeignKey(SubjectOffering,on_delete=models.CASCADE,related_name='schedules')
    teacher = models.ForeignKey('teachers.Teacher',on_delete=models.PROTECT,related_name='class_schedules')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.PROTECT)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = (           
            'subject_offering',
            'day_of_week',
            'start_time',
            'classroom',
        )

   

    def __str__(self):
        return f"{self.subject_offering} - {self.get_day_of_week_display()}"
