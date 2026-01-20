from django.contrib import admin

from.models import (
    School,Section,AcademicClass,Subject,ClassRoom,Schedule,
    ImageGallery,Shift,Gender,Language,Faculty,SubjectAssignment
    )

from.models import ClassTeacher

admin.site.register(Section)
admin.site.register(Gender)
admin.site.register(Shift)
admin.site.register(Language)
admin.site.register(AcademicClass)
admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(Schedule)
admin.site.register(ClassTeacher)
admin.site.register(ImageGallery)

admin.site.register(School)
admin.site.register(Faculty)
admin.site.register(SubjectAssignment)
