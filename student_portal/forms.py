from django import forms

from results.models import ExamType,Exam



class ExamResultForm(forms.Form):
    student_id = forms.CharField(label="Student ID", max_length=20, required=False)
    academic_year = forms.IntegerField(label="Academic Year", required=True)
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        label="Exam Type",
        empty_label="Select Exam Type",
        required=False
    )





class StudentAttendanceFilterForm(forms.Form):
    academic_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class':'form-control'})
    )

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
        widget=forms.NumberInput()
    )
   
  



  

class AcademicYearFilterForm(forms.Form):
   
    academic_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class':'form-control'})
    )

   
