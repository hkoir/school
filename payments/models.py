

from django.db import models
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime, date
import random
import string
from django.utils.timezone import now
from django.db.models import JSONField
from accounts.models import CustomUser


from university_management.models import AcademicSession

class AdmissionFeePolicy(models.Model):
    POLICY_CHOICES = [
        ('basic', 'Basic'),
        ('transport', 'Transport'),
        ('hostel', 'Hostel'),
        ('transport_hostel', 'Transport + Hostel')
    ]
    policy_type = models.CharField(max_length=30, choices=POLICY_CHOICES, default='basic')
    policy_code = models.CharField(max_length=50, null=True, blank=True)
   
    LANGUAGE_CHOICES = [
        ('bangla', 'Bangla'),
        ('english', 'English'),
        ('arabic', 'Arabic'),
    ]
    
    academic_year = models.IntegerField()
    academic_session =models.ForeignKey(AcademicSession,on_delete=models.CASCADE,null=True,blank=True)
    language_version = models.ForeignKey('school_management.Language', on_delete=models.CASCADE,null=True,blank=True)
    student_class = models.ForeignKey('school_management.AcademicClass', on_delete=models.CASCADE, related_name="fees_admission", null=True, blank=True)
    program = models.ForeignKey('university_management.Program', on_delete=models.CASCADE, null=True, blank=True)    
    total_admission_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Policy= {self.policy_code} for {self.academic_year}-{self.academic_session}:class= {self.student_class}-{self.program}:Version= {self.language_version}"

  

    class Meta:
        unique_together = ('academic_year', 'student_class','language_version')

    def generate_policy_code(self):
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{self.academic_year}-{self.student_class.id}-{self.language_version.name[:3].upper()}-{random_string}"
        return code
       
    
    def save(self, *args, **kwargs):
        if not self.policy_code:
            self.policy_code = self.generate_policy_code()          
        super().save(*args, **kwargs)

    def __str__(self):
            return f"Policy={self.policy_code} for year {self.academic_year}-for {self.student_class}"


####################### Pure admission fee model################################

class AdmissionFee(models.Model):  
    FEE_CHOICES = [
        ('registration', 'Registration'), 
        ('tuition', 'Tuition'), 
        ('sports', 'Sports'), 
        ('lab', 'Lab Fees'), 
        ('library', 'Library')
    ]

    admission_fee_policy = models.ForeignKey(AdmissionFeePolicy,on_delete=models.CASCADE,null=True,blank=True,related_name='admission_fees')
    fee_type = models.CharField(max_length=50,choices=FEE_CHOICES,null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_month = models.IntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)], null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)   
  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('admission_fee_policy', 'fee_type')

    def __str__(self):
        return f"Admission Fee for {self.fee_type}"



######################## Pure monthly tuition fee ################################################

class FeeStructure(models.Model):
    LANGUAGE_CHOICES = [
        ('bangla', 'Bangla'),
        ('english', 'English'),
        ('arabic', 'Arabic'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,blank=True)
    academic_year = models.IntegerField()     
    student_class = models.ForeignKey('school_management.AcademicClass', on_delete=models.CASCADE, related_name="fee_structures_class")
    language_version = models.CharField(max_length=20, choices=LANGUAGE_CHOICES,null=True, blank=True)  # Added this field
    monthly_tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    admissionfee_policy = models.ForeignKey(AdmissionFeePolicy,on_delete=models.CASCADE,related_name="admission_fee_policy",null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('academic_year', 'student_class', 'language_version')  

  

    def __str__(self):
        return f"{self.student_class} - {self.language_version} Fees ({self.academic_year})"


######################## This model cover monthly tution fee and admission payment only ################################################

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('partial-paid', 'Partial paid'),
        ('due', 'Due'),
        ('not_due', 'Not Due'),
    ]
   
 
    MONTH_CHOICES = [(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)]
    
    academic_year = models.IntegerField(null=True, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="student_payments")
    month = models.IntegerField(choices=MONTH_CHOICES, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)  # No auto_now_add (Set manually to 25th)
    monthly_tuition_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admission_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)

    admission_fee_items = models.ManyToManyField(AdmissionFee, blank=True, related_name='payments')
    payment_date = models.DateField(auto_now_add=True)
    remaining_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False, null=True, blank=True)
    
    payment_method = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('bikash', 'Bikash'), ('rocket', 'Rocket'), ('nagad', 'Nagad'), ('bank', 'Bank')
    ])
    transaction_id = models.CharField(max_length=50,null=True, blank=True)
    
    monthly_tuition_fee_payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='due')
    admission_fee_payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='due')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS,null=True, blank=True)
    is_all_clear=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def save(self, *args, **kwargs):     
       
    

        self.total_paid = (self.monthly_tuition_fee_paid or Decimal(0.00)) + (self.admission_fee_paid or Decimal(0.00))

        enrollment = self.get_enrollment()
        tuition_fee_due = enrollment.feestructure.monthly_tuition_fee if enrollment and enrollment.feestructure else Decimal(0.00)
        admission_fee_due = self.get_admission_fee_for_month()

        tuition_remaining = max(tuition_fee_due - (self.monthly_tuition_fee_paid or Decimal(0.00)), Decimal(0.00))
        admission_remaining = max(admission_fee_due - (self.admission_fee_paid or Decimal(0.00)), Decimal(0.00))

        self.remaining_due = tuition_remaining + admission_remaining
        if tuition_remaining == 0 and tuition_fee_due > 0:
            self.monthly_tuition_fee_payment_status = 'paid'
        elif (self.monthly_tuition_fee_paid or 0) > 0:
            self.monthly_tuition_fee_payment_status = 'partial-paid'
        else:
            self.monthly_tuition_fee_payment_status = 'due'

        if admission_remaining == 0 and admission_fee_due > 0:
            self.admission_fee_payment_status = 'paid'
        elif (self.admission_fee_paid or 0) > 0:
            self.admission_fee_payment_status = 'partial-paid'
        else:
            self.admission_fee_payment_status = 'due'

        if self.remaining_due == 0:
            self.payment_status = 'paid'
            self.is_all_clear = True
        elif self.total_paid > 0:
            self.payment_status = 'partial-paid'
            self.is_all_clear = False
        else:
            self.payment_status = 'due'
            self.is_all_clear = False

        super().save(*args, **kwargs)


    def get_enrollment(self):
        return self.student.enrolled_students.filter(academic_year=self.academic_year).first()
    
    def get_monthly_due_amount(self):
        enrollment = self.get_enrollment()
        if enrollment and enrollment.feestructure:
            return enrollment.feestructure.monthly_tuition_fee - (self.monthly_tuition_fee_paid or 0)
        return 0

    
    def get_admission_fee_for_month(self):
        enrollment = self.get_enrollment()       
        if not enrollment or not enrollment.feestructure or not enrollment.feestructure.admissionfee_policy:
            return Decimal(0.00)        
        total_admission_fee = Decimal(0.00)
        for fee in enrollment.feestructure.admissionfee_policy.admission_fees.all():
            total_admission_fee += fee.amount
        if any(fee.due_date and fee.due_date.month == self.month for fee in enrollment.feestructure.admissionfee_policy.admission_fees.all()):
            return total_admission_fee
        return Decimal(0.00)


    def get_total_due_for_month(self):
        enrollment = self.get_enrollment()
        if not enrollment or not enrollment.feestructure:
            return Decimal(0.00)

        monthly_fee = enrollment.feestructure.monthly_tuition_fee
        return monthly_fee + self.get_admission_fee_for_month()
    
    def __str__(self):
        return f"Payment for {self.student.name} - {self.month}/{self.academic_year}"
          
 ####################################################################################################
      
    @property
    def is_paid(self):  
        return self.remaining_due == 0      

    @property
    def is_fully_paid(self):  
        return Payment.get_remaining_due_till_today(self.academic_year,self.student) == 0





################################################## New models additions #####################################################

PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('partial', 'Partial paid'),
        ('due', 'Due'),
        ('not_due', 'Not Due'),
    ]


class OnlinePaymentModelMixin(models.Model):
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    ssl_status = models.CharField(max_length=50, blank=True, null=True)
    ssl_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ssl_response = models.JSONField(blank=True, null=True)
    is_online_payment = models.BooleanField(default=False)

    class Meta:
        abstract = True



class TuitionFeePayment(OnlinePaymentModelMixin,models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_tuition_payments')    
    academic_year = models.IntegerField()
    tuition_fee_assignment = models.ForeignKey(
        'students.TuitionFeeAssignment',
        on_delete=models.CASCADE,
        related_name='tuition_payments',
        null=True,
        blank=True
    )
    fee_structure = models.ForeignKey(FeeStructure,on_delete=models.SET_NULL,null=True,blank=True,related_name='tuition_fee_structure')
    month = models.PositiveSmallIntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)],null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)      
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  
            assignment = self.student.student_tuition_assignments.first() if self.student else None
            if assignment and assignment.fee_structure:
                self.total_amount = assignment.fee_structure.monthly_tuition_fee
            else:
                self.total_amount = 0     
        self.due_amount = (self.total_amount or 0) - (self.amount_paid or 0)
      
        if self.amount_paid >= (self.total_amount or 0):
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.month} ({self.payment_status})"
  
   



class AdmissionFeePayment(OnlinePaymentModelMixin,models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_admission_payments',null=True,blank=True)    
    academic_year = models.IntegerField(null=True,blank=True)   
    admission_fee_assignment = models.ForeignKey(
        'students.AdmissionFeeAssignment',
        on_delete=models.CASCADE,
        related_name='admission_payments',
        null=True,
        blank=True
    )
    fee_structure = models.ForeignKey(FeeStructure,on_delete=models.SET_NULL,null=True,blank=True,related_name='admission_fee_structure')
    month = models.PositiveSmallIntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)],null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)      
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    def save(self, *args, **kwargs):      
        if not self.pk:  
            assignment = self.student.student_admission_assignments.first() if self.student else None
            if assignment and assignment.admission_fee:
                self.total_amount = assignment.admission_fee.amount      
        self.due_amount = max(self.total_amount - (self.amount_paid or 0), 0)   
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.student} - due_amount-{self.due_amount}-type:({self.admission_fee_assignment.admission_fee.fee_type})"
    
 
class HostelRoomPayment(OnlinePaymentModelMixin,models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_hostel_payments')
    hostel_room = models.ForeignKey('students.HostelRoom', on_delete=models.CASCADE, related_name='hostel_room_payments')
    hostel_assignment = models.ForeignKey(
        'students.HostelAssignment',
        on_delete=models.CASCADE,
        related_name='hostel_payments',
        null=True,
        blank=True
    )
    academic_year = models.IntegerField()
    month = models.PositiveSmallIntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)],null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)      
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return f"{self.student} -month:{self.month}-due_amount:{self.due_amount}"
    
  
    def save(self, *args, **kwargs):
        if not self.pk: 
            assignment = self.student.student_hostel_assignments.first() if self.student else None
            if assignment and assignment.hostel_room:
                self.total_amount = assignment.hostel_room.fee
        self.due_amount = self.total_amount - Decimal((self.amount_paid or 0))
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'
        super().save(*args, **kwargs)


    class Meta:
        unique_together = ('student', 'hostel_room', 'academic_year', 'month')



class TransportPayment(OnlinePaymentModelMixin,models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_transport_payments')
    transport_route = models.ForeignKey('students.TransportRoute', on_delete=models.CASCADE, related_name='transport_route_payments')
    transport_assignment = models.ForeignKey(
        'students.TransportAssignment',
        on_delete=models.CASCADE,
        related_name='transport_payments',
        null=True,
        blank=True
    )
    academic_year = models.IntegerField()
    month = models.PositiveSmallIntegerField(choices=[(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)],null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} -month:{self.month}-due_amount:{self.due_amount}"

    def save(self, *args, **kwargs):
        if not self.pk: 
            assignment = self.student.student_transport_assignments.first() if self.student else None
            if assignment and assignment.route:
                self.total_amount = assignment.route.fee or 0

        paid = Decimal(self.amount_paid or 0)
        self.due_amount = max(self.total_amount - paid, 0)
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'
        super().save(*args, **kwargs)



class ExamFeePayment(OnlinePaymentModelMixin,models.Model):
    academic_year = models.IntegerField(null=True,blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_exam_fee_payments')
    exam_fee = models.ForeignKey('students.ExamFee', on_delete=models.CASCADE, related_name='exam_fee_payments')
    exam_fee_assignment = models.ForeignKey('students.ExamFeeAssignment', on_delete=models.CASCADE, related_name='exam_fee_payments',null=True,blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)     
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} -exam:{self.exam_fee}-due_amount:{self.due_amount}"

    def save(self, *args, **kwargs):
        if not self.pk: 
            assignment = self.student.student_examfee_assignments.first() if self.student else None
            if assignment and assignment.exam_fee:
                self.total_amount = assignment.exam_fee.amount
        self.due_amount = self.total_amount - Decimal((self.amount_paid or 0))
        if self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'due'
        super().save(*args, **kwargs)

   

    class Meta:
        unique_together = ('student', 'exam_fee')
    def __str__(self):
        return f"{self.student} - {self.exam_fee.exam.name} ({self.payment_status})"



class OtherFeePayment(OnlinePaymentModelMixin,models.Model):
    FEE_TYPE_CHOICES = [     
    
        ('id_card', 'ID Card Fee'),
        ('excursion', 'Excursion Fee'),  
        ('other', 'Other'),
    ]
    academic_year = models.IntegerField(null=True,blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='other_fee_students')
    other_fee_assignment = models.ForeignKey('students.OtherFee', on_delete=models.CASCADE, related_name='other_fee_payments',null=True,blank=True)
    fee_type = models.CharField(max_length=30,choices=FEE_TYPE_CHOICES,null=True,blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)      
    total_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    due_amount = models.DecimalField(max_digits=10,decimal_places=2, default=0.00,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS, 
        default='not_due'
    )
    payment_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} -fee type:{self.fee_type}-due_amount:{self.due_amount}"

    def save(self, *args, **kwargs):
        if self.other_fee_assignment:   
            self.total_amount = self.other_fee_assignment.amount
            self.due_amount = max(self.total_amount - (self.amount_paid or 0), 0)
            if self.amount_paid >= self.total_amount:
                self.payment_status = 'paid'
            elif self.amount_paid > 0:
                self.payment_status = 'partial'
            else:
                self.payment_status = 'due'
        super().save(*args, **kwargs)



FEE_TYPE_CHOICES = [
    ('tuition', 'Tuition Fee'),
    ('admission', 'Admission Fee'),
    ('transport', 'Transport Fee'),
    ('exam', 'Exam Fee'),
    ('library', 'Library Fee'),
    ('lab', 'Lab/Practical Fee'),
    ('hostel', 'Hostel Fee'),
    ('misc', 'Miscellaneous Fee'),
]




class PaymentInvoice(models.Model):
    PAYMENT_METHOD = [
        ('SSLCOMMERZE', 'SSL Commerze'),
        ('Bikash', 'Bikash'),
        ('Nagad', 'Nagad'),
        ('Rocket', 'Rocket'),
        ('CREDIT-CARD', 'Credit card'),
        ('Cash', 'Cash'),
    ]
    academic_year = models.IntegerField(null=True,blank=True)   

    invoice_type = models.CharField(max_length=30, choices=FEE_TYPE_CHOICES)   
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE,related_name='invoice_students',null=True,blank=True)   
    student_enrollment = models.ForeignKey(
       'students.StudentEnrollment',
        on_delete=models.CASCADE,
        related_name='invoices',null=True,blank=True
    )
    admission_fee_items = models.ManyToManyField(AdmissionFee, blank=True)  
    tuition_month = models.PositiveSmallIntegerField(null=True, blank=True)  # 1=Jan, ..., 12=Dec
    extra_data = JSONField(null=True, blank=True)
    tran_id = models.CharField(max_length=100, unique=True)   

    amount = models.DecimalField(max_digits=10,decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)  

    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    due_amount = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)

    description = models.TextField()
    
    tution_payment_assignment = models.ForeignKey('students.TuitionFeeAssignment', on_delete=models.SET_NULL, null=True, blank=True,related_name='invoice_tuition')
    admission_fee_payment_assignment = models.ForeignKey('students.AdmissionFeeAssignment', on_delete=models.SET_NULL, null=True, blank=True,related_name='invoice_admission')
    hostel_assignment = models.ForeignKey('students.HostelAssignment', on_delete=models.SET_NULL, null=True, blank=True,related_name='invoice_hostels')
    transport_assignment = models.ForeignKey('students.TransportAssignment', on_delete=models.SET_NULL, null=True, blank=True,related_name='invoice_transports')
    exam_fee_assignment = models.ForeignKey('students.ExamFeeAssignment', on_delete=models.SET_NULL, null=True, blank=True)
    other_fee_assignment = models.ForeignKey('students.OtherFee', on_delete=models.SET_NULL, null=True, blank=True,related_name='invoice_otherfees')
   
    tuition_payments = models.ManyToManyField('payments.TuitionFeePayment', blank=True, related_name='invoice_tuitions')
    transport_payments = models.ManyToManyField('payments.TransportPayment', blank=True, related_name='invoice_transports')
    hostel_payments = models.ManyToManyField('payments.HostelRoomPayment', blank=True, related_name='invoice_hostels')
    admission_payments = models.ManyToManyField('payments.AdmissionFeePayment', blank=True, related_name='invoice_adissions')
    exam_payments = models.ManyToManyField('payments.ExamFeePayment', blank=True, related_name='invoice_exam_fees')
    other_payments = models.ManyToManyField('payments.OtherFeePayment', blank=True, related_name='invoice_other_fees')

    payment_method = models.CharField(max_length=50,choices=PAYMENT_METHOD,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=Payment.PAYMENT_STATUS, 
        default='not_due',null=True,blank=True
    )
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def apply_taxes(self):     
 
        from core.models import TaxPolicy, ServiceTaxPolicy 
        from decimal import Decimal, ROUND_HALF_UP
        total = Decimal(self.amount or 0)  
        amount_after_vat =Decimal(0)
        service_policy = None
        
        if hasattr(self, "invoice_type") and self.invoice_type:
            service_policy = ServiceTaxPolicy.objects.filter(name=self.invoice_type).first() 
        if not service_policy:
            tax = TaxPolicy.objects.filter(is_active=True).first()
            if not tax:
                self.vat_amount = Decimal(0)
                self.ait_amount = Decimal(0)
                self.net_amount = total
                return

            service_policy = tax
  
        vat_rate = Decimal(service_policy.vat_rate or 0) / 100
        ait_rate = Decimal(service_policy.ait_rate or 0) / 100
        vat_type = service_policy.vat_type.lower()
        ait_type = service_policy.ait_type.lower()

        # ------------------- VAT Calculation -------------------
        if vat_type == "inclusive":
            base = (total / (1 + vat_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.vat_amount = (total - base).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            amount_after_vat = base
        elif vat_type == "exclusive":
            self.vat_amount = (total * vat_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            amount_after_vat = total
        else:  # exempt
            self.vat_amount = Decimal(0)
            amount_after_vat = total

        # ------------------- AIT Calculation -------------------
        if ait_type == "inclusive":
            base2 = (amount_after_vat / (1 + ait_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.ait_amount = (amount_after_vat - base2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.net_amount = base2
        elif ait_type == "exclusive":
            self.ait_amount = (amount_after_vat * ait_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.net_amount = (amount_after_vat - self.ait_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:  # exempt
            self.ait_amount = Decimal(0)
            self.net_amount = amount_after_vat

    def save(self, *args, **kwargs):
        if not self.tran_id:
            self.tran_id = f"txn_{now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_invoice_type_display()} Invoice #{self.tran_id} ({self.student})"





      

