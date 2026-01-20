
from django import forms
from.models import Grade,Result,StudentFinalResult,ExamType,Exam
from school_management.utils import GENDER_CHOICES,SHIFT_CHOICES,LANGUAGE_CHOICES
from school_management.models import Subject,AcademicClass,Section,Language
from students.models import Student 
from .models import Exam




class GradeForm(forms.ModelForm):
    class Meta:
        model =Grade
        exclude=['user']
        




class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'academic_year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter exam name'}),
            'academic_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025'}),
        }






class ExamCreationForm(forms.ModelForm):
    academic_class = forms.ModelChoiceField(
        queryset=AcademicClass.objects.all(),
        required=True,
        label="Class"
    )
    language_version = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        required=True,
        label="Language"
    )

    exam_fee_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label="Exam Fee Amount"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )

    class Meta:
        model = Exam
        fields = ['name', 'academic_year','exam_start_date']

        widgets={
            'exam_start_date':forms.DateInput(attrs={"type":'date'})
        }






class ExamResultForm(forms.Form):
    student_id = forms.CharField(label="Student ID", max_length=20, required=False)
    academic_year = forms.IntegerField(label="Academic Year", required=False)
    exam_type = forms.ModelChoiceField(
        queryset=ExamType.objects.all(),
        label="Exam Type",
        empty_label="Select Exam Type",
        required=False
    )

    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        label="Exam",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'exam'})
    )

        
class ResultForm(forms.ModelForm):
    exam = forms.ModelChoiceField(
    queryset=Exam.objects.all(),
    label="Exam",
    required=True,
    widget=forms.Select(attrs={'class': 'form-control'})  # REMOVE 'id': 'exam'
)
    exam_type = forms.ModelChoiceField(
        queryset=ExamType.objects.all(),  # Empty initially
        label="Exam Type",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'exam_type'})
    )

    class Meta:
        model = Result
        exclude = ['user','status','final_result']
        widgets = {
         
            'student': forms.Select(attrs={'class': 'form-control', 'id': 'student-dropdown'}),           
            'academic_class': forms.Select(attrs={'class': 'form-control', 'id': 'academic-class'}),
            'section': forms.Select(attrs={'class': 'form-control', 'id': 'section'}),
            'faculty': forms.Select(attrs={'class': 'form-control', 'id': 'faculty'}),

            'subject': forms.Select(attrs={
                'class': 'form-control',
                  'id': 'subject',                
                  }),         

            # 'exam_type': forms.Select(attrs={'class': 'form-control', 'id': 'exam_type'}),
            'exam_date': forms.DateInput(attrs={'type': 'date','id':'exam_date'}),
            'exam_marks': forms.NumberInput(attrs={'class': 'form-control', 'id': 'exam_marks'}),

        }

    



class ExamTypeForm(forms.ModelForm):   

    class Meta:
        model = ExamType
        exclude = ['user']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
        }
   


class StudentTranscriptFilterForm(forms.Form):
    student_id = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_id'].choices = [
            (student.student_id, student.name) for student in Student.objects.all()
        ]







class ClassTopperReportFilterForm(forms.Form):
  
    academic_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class':'form-control'})
    )



    class_name = forms.ModelChoiceField(
        queryset=AcademicClass.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
  
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class':'form-control'})
    )
  

    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    shift= forms.ChoiceField(
        choices=[('', 'select')] + SHIFT_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class_gender= forms.ChoiceField(
        choices=[('', 'select')] + GENDER_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    version= forms.ChoiceField(
         choices=[('', 'select')] + LANGUAGE_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )





   
class AggregateReportFilterForm(forms.Form):
  
    academic_year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'class':'form-control'})
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
        choices=[('', 'select')] + SHIFT_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class_gender= forms.ChoiceField(
        choices=[('', 'select')] + GENDER_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    version= forms.ChoiceField(
         choices=[('', 'select')] + LANGUAGE_CHOICES[1:],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


   
