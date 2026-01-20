
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from school_management.models import Subject,School,Faculty,Section,AcademicClass
from.models import ClassRoom,Subject,Schedule,ImageGallery
from.models import AcademicClass,Subject,SubjectAssignment



class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        exclude=['user']
        widgets={
            'address':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            }),
            'date_of_establishment':forms.DateInput(attrs={'type':'date'})
        }



class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        exclude=['user']
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            })
        }
       



class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude=['user','class_assignment']
       


class ClassAssignmentorm(forms.ModelForm):
    class Meta:
        model = AcademicClass
        exclude=['user']
       


from django.forms import modelformset_factory

class SubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = SubjectAssignment
        fields = ['subject', 'academic_class']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'academic_class': forms.Select(attrs={'class': 'form-select'}),
        }


SubjectAssignmentFormSet = modelformset_factory(
    SubjectAssignment,
    form=SubjectAssignmentForm,
    extra=3, 
    can_delete=True  
)

class SubjectAssignmentSimpleForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))



class ImageGalleryForm(forms.ModelForm):
    class Meta:
        model = ImageGallery
        exclude=['user']
      

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        exclude = ['user']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }



class ClassForm(forms.ModelForm):
    class Meta:
        model = AcademicClass
        exclude=['user']
        widgets={
            'description':forms.Textarea(attrs={
                'class':'form-control',
                'style':'height:50px'
            })
        }
       

class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        exclude=['user']



from django import forms
from .models import Subject, AcademicClass, Faculty



class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'faculty']  
       
class ImageGalleryForm(forms.ModelForm):
    class Meta:
        model = ImageGallery
        exclude=['user']
       
       
             






































