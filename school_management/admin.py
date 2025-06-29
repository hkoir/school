from django.contrib import admin

from.models import Section,AcademicClass,Subject,ClassRoom,SubjectAssignment,Schedule,ImageGallery

admin.site.register(Section)
admin.site.register(AcademicClass)
admin.site.register(Subject)
admin.site.register(ClassRoom)
admin.site.register(SubjectAssignment)
admin.site.register(Schedule)

admin.site.register(ImageGallery)