from django import forms
from django.forms import inlineformset_factory
from school_management.models import Subject
from .models import StudentEnrollment
from .models import Guardian, Student
from attendance.models import AttendancePolicy

from django import forms
from .models import StudentEnrollment, Subject
from django.core.exceptions import ValidationError


class StudentEnrollmentForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        exclude = ['user']
        widgets = {
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'academic_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'student_class': forms.Select(attrs={'class': 'form-control', 'id': 'id_student_class'}),
 	    'academic_class': forms.Select(attrs={'class': 'form-control', 'id': 'id_academic_class'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

   



class AttendancePolicyForm(forms.ModelForm):
    class Meta:
        model = AttendancePolicy
        exclude=['user']


       

class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        exclude=['user']
        widgets={
            'address':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            })
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude=['student_id']
        widgets={
            'address':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),
            'date_enrolled':forms.DateInput(attrs={'type':'date'}),
            'date_of_birth':forms.DateInput(attrs={'type':'date'})
        }




class StudentFilterForm(forms.Form):
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
  
 
    student_id = forms.CharField(
        label='Student ID',
        required=False,
       
    )   
