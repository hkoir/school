
from django import forms
from django.forms import modelformset_factory
from django.forms import inlineformset_factory
from .models import (
    StudentSubjectResult,StudentTermRegistration, StudentSubjectEnrollment,
    Exam, ExamSchedule,VarsityStudentEnrollment,UniversityPayment,SubjectOffering
    )



class StudentEnrollmentForm(forms.ModelForm):
    class Meta:
        model = VarsityStudentEnrollment
        fields = [
            'student',
            'academic_session',
            'program',
            'language',
          
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'academic_session': forms.Select(attrs={'class': 'form-select'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'attendance_policy': forms.Select(attrs={'class': 'form-select'}),
        }



class StudentTermRegistrationForm(forms.ModelForm):
    class Meta:
        model = StudentTermRegistration
        fields = [
            'level',
            'term',           
            'academic_year'
        ]
        widgets = {
            'term': forms.Select(attrs={'class': 'form-control', 'id': 'term-select'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }



class StudentSubjectEnrollmentForm(forms.ModelForm):
    class Meta:
        model = StudentSubjectEnrollment
        fields = ['subject_offering']

    def __init__(self, *args, **kwargs):
        subject_qs = kwargs.pop('subject_qs', None)
        super().__init__(*args, **kwargs)

        if subject_qs is not None:
            self.fields['subject_offering'].queryset = subject_qs


from django.forms.models import BaseInlineFormSet

class BaseStudentSubjectEnrollmentFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.subject_qs = kwargs.pop('subject_qs', None)
        super().__init__(*args, **kwargs)

        for form in self.forms:
            if self.subject_qs is not None:
                form.fields['subject_offering'].queryset = self.subject_qs


StudentSubjectEnrollmentFormSet = inlineformset_factory(
    StudentTermRegistration,
    StudentSubjectEnrollment,
    form=StudentSubjectEnrollmentForm,
    formset=BaseStudentSubjectEnrollmentFormSet,
    extra=1,
    can_delete=True
)




class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'institution',
            'academic_session',
            'academic_year',
            'program',
            'level',
            'term',
            'exam_type',
            'start_date',
            'end_date',
            'is_published',
        ]
        widgets = {
                'start_date': forms.DateInput(attrs={'type':'date'}),
                'end_date': forms.DateInput(attrs={'type':'date'}),
            
            }



class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = [
            'subject_offering',
            'exam_date',
            'start_time',
            'end_time',
            'venue',
            'max_marks',
        ]
        widgets = {
                'exam_date': forms.DateInput(attrs={'type':'date'}),
                'start_time': forms.DateInput(attrs={'type':'time'}),
                'end_time': forms.DateInput(attrs={'type':'time'}),
            
            }

ExamScheduleFormSet = inlineformset_factory(
    Exam,
    ExamSchedule,
    form=ExamScheduleForm,
    extra=1,
    can_delete=True
)



from django import forms
from django.forms import BaseModelFormSet
from university_management.models import StudentSubjectResult, SubjectOffering
class StudentSubjectResultForm(forms.ModelForm):
    class Meta:
        model = StudentSubjectResult
        fields = [
            'subject_offering',
            'marks_obtained',           
            'is_absent',
            'is_published',
        ]
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'subject_offering': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Pop filtered queryset if provided
        subject_qs = kwargs.pop('subject_qs', None)
        super().__init__(*args, **kwargs)
        if subject_qs is not None:
            self.fields['subject_offering'].queryset = subject_qs
        else:
            self.fields['subject_offering'].queryset = SubjectOffering.objects.none()


class BaseStudentSubjectResultFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        subject_qs = kwargs.pop('subject_qs', None)
        super().__init__(*args, **kwargs)      
        for form in self.forms:
            if subject_qs is not None:
                form.fields['subject_offering'].queryset = subject_qs      
        if subject_qs is not None:
            self.empty_form.fields['subject_offering'].queryset = subject_qs


StudentSubjectResultFormSet = modelformset_factory(
    StudentSubjectResult,
    form=StudentSubjectResultForm,
    formset=BaseStudentSubjectResultFormSet,
    extra=1,
    can_delete=True
)



class UniversityPaymentForm(forms.ModelForm):
    class Meta:
        model = UniversityPayment
        fields = ['invoice', 'admission_paid','tuition_paid','tax_policy', 'payment_method', 'transaction_id']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'admission_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tuition_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional for cash'}),
        }



from .models import ClassSchedule
class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = [
            'session', 'subject_offering',
            'teacher', 'classroom', 'day_of_week',
            'start_time', 'end_time'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        subject_qs = kwargs.pop('subject_qs', SubjectOffering.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['subject_offering'].queryset = subject_qs


class BaseClassScheduleFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.subject_qs = kwargs.pop('subject_qs', SubjectOffering.objects.none())
        super().__init__(*args, **kwargs)
        # apply to existing forms
        for form in self.forms:
            form.fields['subject_offering'].queryset = self.subject_qs
        # apply to empty form (for JS add-row)
        self.empty_form.fields['subject_offering'].queryset = self.subject_qs


ClassScheduleFormSet = modelformset_factory(
    ClassSchedule,
    form=ClassScheduleForm,
    formset=BaseClassScheduleFormSet,
    extra=1,
    can_delete=True
)
