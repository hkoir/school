from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from school_management.models import Subject,School,Faculty,Section,AcademicClass
from django.core.exceptions import ValidationError
from .models import Schedule,ImageGallery
from.models import ClassRoom,Subject,Schedule,TeachingAssignment,ImageGallery
from.models import ClassAssignment,SubjectAssignment



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
        exclude=['user']
       


class ClassAssignmentorm(forms.ModelForm):
    class Meta:
        model = ClassAssignment
        exclude=['user']
       


class SubjectAssignmentorm(forms.ModelForm):
    class Meta:
        model = SubjectAssignment
        exclude=['user']
           





class ImageGalleryForm(forms.ModelForm):
    class Meta:
        model = ImageGallery
        exclude=['user']
      

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        exclude=['user']
        widgets={
            'start_time':forms.TimeInput(attrs={'type':'time'}),
            'end_time':forms.TimeInput(attrs={'type':'time'})
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



class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        exclude=['user']
        widgets={
            'start_time':forms.TimeInput(attrs={'type':'time'}),
            'end_time':forms.TimeInput(attrs={'type':'time'})
        }



class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        exclude=['user']
       
class ImageGalleryForm(forms.ModelForm):
    class Meta:
        model = ImageGallery
        exclude=['user']
       
       
             



















