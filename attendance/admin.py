from django.contrib import admin

from.models import Attendance,AttendanceLog,AttendancePolicy,Weekday

admin.site.register(Attendance)
admin.site.register(AttendanceLog)
admin.site.register(AttendancePolicy)
admin.site.register(Weekday)
