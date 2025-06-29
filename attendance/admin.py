from django.contrib import admin

from.models import Attendance,AttendanceLog,AttendancePolicy

admin.site.register(Attendance)
admin.site.register(AttendanceLog)
admin.site.register(AttendancePolicy)