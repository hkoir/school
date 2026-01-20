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





###############################################################################

from .models import (
    ExamFee, ExamFeeAssignment, TransportRoute, TransportAssignment,
    RoomType, Hostel, HostelRoom, HostelAssignment, OtherFee,
    TuitionFeeAssignment,AdmissionFeeAssignment
)



class TuitionAssignmentForm(forms.ModelForm):
    class Meta:
        model = TuitionFeeAssignment
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),       
            'start_date':forms.DateInput(attrs={'type':'date'}),
            'end_date':forms.DateInput(attrs={'type':'date'}) ,
            'student': forms.Select(attrs={'id': 'id_student', 'class': 'form-select'}),
            'student_enrollment': forms.Select(attrs={'id': 'id_student_enrollment', 'class': 'form-select'}),
           
        }

class AdmissionAssignmentForm(forms.ModelForm):
    class Meta:
        model = AdmissionFeeAssignment
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),       
            'start_date':forms.DateInput(attrs={'type':'date'}),
            'end_date':forms.DateInput(attrs={'type':'date'})  
           
        }





class ExamFeeForm(forms.ModelForm):
    class Meta:
        model = ExamFee
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }


class ExamFeeAssignmentForm(forms.ModelForm):
    class Meta:
        model = ExamFeeAssignment
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }

class TransportRouteForm(forms.ModelForm):
    class Meta:
        model = TransportRoute
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }

class TransportAssignmentForm(forms.ModelForm):
    class Meta:
        model = TransportAssignment
        fields= '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),       
            'start_date':forms.DateInput(attrs={'type':'date'}),
            'end_date':forms.DateInput(attrs={'type':'date'})  
           
        }

class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }

class HostelForm(forms.ModelForm):
    class Meta:
        model = Hostel
        fields = '__all__'
        widgets={
            'address':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }

class HostelRoomForm(forms.ModelForm):
    class Meta:
        model = HostelRoom
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }

class HostelAssignmentForm(forms.ModelForm):
    class Meta:
        model = HostelAssignment
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),       
            'start_date':forms.DateInput(attrs={'type':'date'}),
             'end_date':forms.DateInput(attrs={'type':'date'})
           
        }

class OtherFeeForm(forms.ModelForm):
    class Meta:
        model = OtherFee
        fields = '__all__'
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),         
           
        }
