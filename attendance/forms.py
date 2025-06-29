from django import forms
from.models import Weekday,AttendancePolicy,Attendance,AttendanceLog
from django import forms
from school_management.models import AcademicClass, Section,Subject
from school_management.utils import SHIFT_CHOICES,GENDER_CHOICES,LANGUAGE_CHOICES
from students.models import Student
from django_select2.forms import ModelSelect2Widget




class WeekdayForm(forms.ModelForm):
    class Meta:
        model =Weekday
        exclude=['user']

class AttendancePolicyForm(forms.ModelForm):
    class Meta:
        model =AttendancePolicy
        exclude=['user']
        widgets={
            'check_in_time':forms.TimeInput(attrs={'type':'time'}),
            'check_out_time':forms.TimeInput(attrs={'type':'time'}),
            'check_in_threshold':forms.TimeInput(attrs={'type':'time'}),
            'check_out_threshold':forms.TimeInput(attrs={'type':'time'}),
            'absent_threshold':forms.TimeInput(attrs={'type':'time'}),

            'weekened': forms.SelectMultiple(attrs={
                'class': 'form-control',  # Bootstrap styling
                'style': 'width: 300px;',  # Increase width
            }),
        }
        help_texts = {
            'weekened': 'Hold down "Ctrl" (Windows) or "Command" (Mac) to select multiple days.',
        }

        def __init__(self, *args, **kwargs):
            super(AttendancePolicyForm, self).__init__(*args, **kwargs)
            self.fields['check_in_time'].widget.attrs.update({'id': 'id_check_in_time'})
            self.fields['check_out_time'].widget.attrs.update({'id': 'id_check_out_time'})
            self.fields['check_in_threshold'].widget.attrs.update({'id': 'id_check_in_threshold'})
            self.fields['check_out_threshold'].widget.attrs.update({'id': 'id_check_out_threshold'})
            self.fields['is_dynamic'].widget.attrs.update({'id': 'id_is_dynamic'})



            

class AttendanceForm(forms.ModelForm):
    class Meta:
        model =Attendance
        exclude=['user']
        widgets={
            'remarks':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),
            'date':forms.TimeInput(attrs={'type':'datetime-local'}),
            'first_check_in':forms.TimeInput(attrs={'type':'time'}),
            'last_check_out':forms.TimeInput(attrs={'type':'time'}),
        }

class AttendanceLogForm(forms.ModelForm):
    class Meta:
        model =AttendanceLog
        exclude=['user']
        widgets={
            'check_in_time':forms.TimeInput(attrs={'type':'time'}),
            'check_out_time':forms.TimeInput(attrs={'type':'time'}),
            'date':forms.DateInput(attrs={'type':'date'}),
        }

        




class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date','class':'form-control'})
    )

    end_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date','class':'form-control'})
    )

    days = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'type': 'date','class':'form-control'})
    )

    date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date','class':'form-control'})
    )

    academic_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class':'form-control'})
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class':'form-control'})
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class':'form-control'})
    )
    class_name = forms.ModelChoiceField(
        queryset=AcademicClass.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    shift= forms.ChoiceField(
        choices=SHIFT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class_gender= forms.ChoiceField(
         choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    version= forms.ChoiceField(
         choices=LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


   
