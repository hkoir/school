from django.contrib import admin

from.models import Result,StudentFinalResult,ExamType,Exam

admin.site.register(Result)
admin.site.register(StudentFinalResult)
admin.site.register(Exam)



from django import forms
class ExamForm(forms.ModelForm):
    class Meta:
        model = ExamType
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set input formats to accept HTML5 time inputs (e.g. "14:30")
        self.fields['start_time'].input_formats = ['%H:%M', '%I:%M %p', '%I %p']
        self.fields['end_time'].input_formats = ['%H:%M', '%I:%M %p', '%I %p']

@admin.register(ExamType)
class ExamAdmin(admin.ModelAdmin):
    form = ExamForm