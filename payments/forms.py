from django import forms
from .models import FeeStructure



class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        exclude=['user']




from.models import AdmissionFeePolicy,AdmissionFee

class AdmissionfeePolicyForm(forms.ModelForm):
    class Meta:
        model = AdmissionFeePolicy
        exclude=['user','policy_code']





class AdmissionfeeForm(forms.ModelForm):
    class Meta:
        model = AdmissionFee
        exclude=['user']
        widgets={
           
            'due_date':forms.DateInput(attrs={'type':'date'})
        }




from datetime import date
from django import forms
from datetime import date

class FeePaymentForm(forms.Form):
    fee_types = forms.MultipleChoiceField(
        choices=[
            ('tuition_fees', 'Tuition Fee'), 
            ('admission_fee', 'Admission Fee')
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    tuition_months = forms.MultipleChoiceField(
        choices=[],  # empty default, will be set dynamically
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    admission_fee_items = forms.ModelMultipleChoiceField(
        queryset=AdmissionFee.objects.none(),  # empty default
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, student=None, tuition_months_choices=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Set tuition_months choices dynamically if provided
        if tuition_months_choices is not None:
            self.fields['tuition_months'].choices = tuition_months_choices
        else:
            # fallback to all months if not provided
            self.fields['tuition_months'].choices = [(i, date(1900, i, 1).strftime('%B')) for i in range(1, 13)]

        # Set admission_fee_items queryset based on student's current enrollment
        if student:
            current_year = 2025  # You can change to dynamic year if needed
            enrollment = student.enrolled_students.filter(academic_year=current_year).first()
            if enrollment and enrollment.feestructure and enrollment.feestructure.admissionfee_policy:
                policy = enrollment.feestructure.admissionfee_policy
                self.fields['admission_fee_items'].queryset = AdmissionFee.objects.filter(admission_fee_policy=policy)
            else:
                self.fields['admission_fee_items'].queryset = AdmissionFee.objects.none()
        else:
            self.fields['admission_fee_items'].queryset = AdmissionFee.objects.none()


from .models import Payment
from django.db.models import Sum

class PaymentForm(forms.ModelForm):
    monthly_fee_due = forms.DecimalField(label="Monthly Tuition Fee Due", required=False, disabled=True)
    admission_fee_due = forms.DecimalField(label="Admission Fee Due (Total till this month)", required=False, disabled=True)

    class Meta:
        model = Payment
        fields = [
            'academic_year', 'month', 'due_date',
            'monthly_fee_due', 'admission_fee_due',
            'monthly_tuition_fee_paid', 'admission_fee_paid',
            'payment_method', 'transaction_id'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student      
        academic_year = self.initial.get('academic_year') or self.data.get('academic_year') or getattr(self.instance, 'academic_year', None)
        month = self.initial.get('month') or self.data.get('month') or getattr(self.instance, 'month', None)

        if student and academic_year and month:
            try:
                academic_year = int(academic_year)
                month = int(month)
                enrollment = student.enrolled_students.filter(academic_year=academic_year).first()
                if enrollment and enrollment.feestructure:       
                    self.fields['monthly_fee_due'].initial = enrollment.feestructure.monthly_tuition_fee                    
                    policy = enrollment.feestructure.admissionfee_policy
                    if policy:
                        admission_due = sum(fee.amount for fee in policy.admission_fees.filter(due_month__lte=month))                        
                        from .models import Payment
                        total_paid = Payment.objects.filter(
                            student=student,
                            academic_year=academic_year
                        ).aggregate(total=Sum('admission_fee_paid'))['total'] or 0

                        self.fields['admission_fee_due'].initial = max(admission_due - total_paid, 0)
            except ValueError:
                pass  # If month or year are not valid integers, skip





class ManualPaymentForm(forms.Form):
    FEE_TYPE_CHOICES = [
        ('tuition_fees', 'Tuition Fees'),
        ('admission_fee', 'Admission Fee'),
    ]

    fee_types = forms.MultipleChoiceField(
        label="Select Fee Type(s)",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=FEE_TYPE_CHOICES,
    )

    tuition_months = forms.MultipleChoiceField(
        label="Select Tuition Months",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[]  # Set dynamically
    )
    admission_fee_items = forms.ModelMultipleChoiceField(
        label="Select Admission Fee Items",
        required=False,
        queryset=AdmissionFee.objects.none(),
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, student=None, tuition_months_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tuition_months_choices:
            self.fields['tuition_months'].choices = tuition_months_choices
        if student:
            self.student = student





class PaymentSearchForm(forms.Form):
    student_id = forms.CharField(label="Student ID", required=True)
    academic_year = forms.IntegerField(label="Academic Year", required=True)





from students.models import Student

class StudentSelectForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        label="Select Student",
    )
    student_id_input = forms.CharField(
        max_length=20,
        required=False,
        label="Or Enter Student ID Manually",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. STU20250012'})
    )

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        student_id_input = cleaned_data.get("student_id_input")

        if not student and not student_id_input:
            raise forms.ValidationError("Please select a student or enter a student ID.")

        return cleaned_data









#################################### new addition ######################################
from .models import HostelRoomPayment, TransportPayment, ExamFeePayment, OtherFeePayment,TuitionFeePayment,AdmissionFeePayment

PAYMENT_TYPE_CHOICES = [

    ('tuition', 'Tuition fee'),
    ('admission', 'Admission fee'),
    ('hostel', 'Hostel Room Payment'),
    ('transport', 'Transport Payment'),
    ('exam', 'Exam Fee Payment'),
    ('other', 'Other Fee Payment'),
]

class PaymentTypeForm(forms.Form):
    payment_type = forms.ChoiceField(choices=PAYMENT_TYPE_CHOICES, label="Select Payment Type")


class TuitionFeePaymentForm(forms.ModelForm):
    class Meta:
        model = TuitionFeePayment
        fields = ['student','academic_year','fee_structure', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }



class AdmissionFeePaymentForm(forms.ModelForm):
    class Meta:
        model = AdmissionFeePayment
        fields = ['student','fee_structure', 'academic_year', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
             'student': forms.Select(attrs={'id': 'id_student', 'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'id': 'id_fee_structure', 'class': 'form-select'}),
            
        }


class HostelRoomPaymentForm(forms.ModelForm):
    class Meta:
        model = HostelRoomPayment
        fields = ['student', 'hostel_room', 'academic_year', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class TransportPaymentForm(forms.ModelForm):  
    class Meta:
        model = TransportPayment
        fields = ['student', 'transport_route', 'academic_year', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class ExamFeePaymentForm(forms.ModelForm):
    class Meta:
        model = ExamFeePayment
        fields = ['student', 'exam_fee', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class OtherFeePaymentForm(forms.ModelForm):
    class Meta:
        model = OtherFeePayment
        fields = ['student', 'other_fee_assignment', 'amount_paid', 'payment_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
