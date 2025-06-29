from django.db import models

from school_management.models import AcademicClass
from accounts.models import CustomUser
from django.core.exceptions import ValidationError

from django.db import models
from decimal import Decimal


from django.db.models import Sum
from decimal import Decimal
from datetime import datetime, date
import random
import string









class AdmissionFeePolicy(models.Model):
    policy_code = models.CharField(max_length=50, null=True, blank=True)
    
    LANGUAGE_CHOICES = [
        ('bangla', 'Bangla'),
        ('english', 'English'),
        ('arabic', 'Arabic'),
    ]
    
    academic_year = models.IntegerField()
    language_version = models.CharField(max_length=100, choices=LANGUAGE_CHOICES)
    student_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name="fees_admission", null=True, blank=True)
    total_admission_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Policy= {self.policy_code} for {self.academic_year}:class= {self.student_class}:Version= {self.language_version}"

  

    class Meta:
        unique_together = ('academic_year', 'student_class','language_version')

    def generate_policy_code(self):
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{self.academic_year}-{self.student_class.id}-{self.language_version[:3].upper()}-{random_string}"
        return code
       
    
    def save(self, *args, **kwargs):
        if not self.policy_code:
            self.policy_code = self.generate_policy_code()          
        super().save(*args, **kwargs)

    def __str__(self):
            return f"Policy={self.policy_code} for year {self.academic_year}-for {self.student_class}"



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




class FeeStructure(models.Model):
    LANGUAGE_CHOICES = [
        ('bangla', 'Bangla'),
        ('english', 'English'),
        ('arabic', 'Arabic'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,blank=True)
    academic_year = models.IntegerField()  # Example: 2024, 2025
    student_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE, related_name="fee_structures_class")
    language_version = models.CharField(max_length=20, choices=LANGUAGE_CHOICES,null=True, blank=True)  # Added this field
    monthly_tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    admissionfee_policy = models.ForeignKey(AdmissionFeePolicy,on_delete=models.CASCADE,related_name="admission_fee_policy",null=True, blank=True)
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('academic_year', 'student_class', 'language_version')  

   

    def __str__(self):
        return f"{self.student_class} - {self.language_version} Fees ({self.academic_year})"





class Payment(models.Model):
    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('partial-paid', 'Partial paid'),
        ('due', 'Due')
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


   
    def save(self, *args, **kwargs):
        related_admission_payments = self.admission_fee_payments.all()
        if related_admission_payments.exists():
            self.admission_fee_paid = related_admission_payments.aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal(0.00)
        self.total_paid = (self.monthly_tuition_fee_paid or Decimal(0.00)) + (self.admission_fee_paid or Decimal(0.00))

        enrollment = self.get_enrollment()
        tuition_fee_due = enrollment.feestructure.monthly_tuition_fee if enrollment and enrollment.feestructure else Decimal(0.00)
        admission_fee_due = self.get_admission_fee_for_month()

        # Remaining due per category
        tuition_remaining = max(tuition_fee_due - (self.monthly_tuition_fee_paid or Decimal(0.00)), Decimal(0.00))
        admission_remaining = max(admission_fee_due - (self.admission_fee_paid or Decimal(0.00)), Decimal(0.00))

        # Overall remaining due
        self.remaining_due = tuition_remaining + admission_remaining

        # Status: Tuition Fee
        if tuition_remaining == 0 and tuition_fee_due > 0:
            self.monthly_tuition_fee_payment_status = 'paid'
        elif (self.monthly_tuition_fee_paid or 0) > 0:
            self.monthly_tuition_fee_payment_status = 'partial-paid'
        else:
            self.monthly_tuition_fee_payment_status = 'due'

        # Status: Admission Fee
        if admission_remaining == 0 and admission_fee_due > 0:
            self.admission_fee_payment_status = 'paid'
        elif (self.admission_fee_paid or 0) > 0:
            self.admission_fee_payment_status = 'partial-paid'
        else:
            self.admission_fee_payment_status = 'due'

        # Overall Payment Status
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





class AdmissionFeePayment(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='admission_fee_payments')
    admission_fee_item = models.ForeignKey(AdmissionFee, on_delete=models.CASCADE,related_name='admission_fee_items')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(
        max_length=20,
        choices=Payment.PAYMENT_STATUS,  # reuse choices from Payment model
        default='due'
    )
    
    class Meta:
        unique_together = ('payment', 'admission_fee_item')


from django.utils.timezone import now
from django.db.models import JSONField

class PaymentInvoice(models.Model):
    INVOICE_TYPES = [
        ('tuition_fees', 'Tuition Fee'),
        ('admission_fee', 'Admission Fee'),       
    ]
    invoice_type = models.CharField(max_length=30, choices=INVOICE_TYPES)
    admission_fee_items = models.ManyToManyField(AdmissionFee, blank=True)  
    tuition_month = models.PositiveSmallIntegerField(null=True, blank=True)  # 1=Jan, ..., 12=Dec
    extra_data = JSONField(null=True, blank=True)
    tran_id = models.CharField(max_length=100, unique=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)   
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    description = models.TextField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.tran_id:            
            self.tran_id = f"txn_{now().strftime('%Y%m%d%H%M%S')}_{self.student.id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_type} Invoice #{self.tran_id} for {self.student.name}"






      
