from django import forms
from.models import Teacher





class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        exclude = ['employee_code','teacher_id', 'resignation_date', 'lateness_salary_deductions','is_active','active']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),          
            'office_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'office_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'employee_photo_ID': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_education_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_NID': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter full address...',
                'style': 'height:80px'
            }),
            'is_roster_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_senior_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
       




class TeacherFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
  
 
    teacher_id = forms.CharField(
        label='Student ID',
        required=False,
       
    )   
