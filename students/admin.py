from django.contrib import admin

from.models import Guardian,Student,StudentEnrollment,ExamFeeAssignment,ExamFee,TransportAssignment
from.models import TuitionFeeAssignment,AdmissionFeeAssignment,HostelAssignment,OtherFee
admin.site.register(Guardian)
admin.site.register(Student)
admin.site.register(StudentEnrollment)

admin.site.register(ExamFee)
admin.site.register(ExamFeeAssignment)
admin.site.register(TransportAssignment)

admin.site.register(TuitionFeeAssignment)
admin.site.register(AdmissionFeeAssignment)
admin.site.register(HostelAssignment)
admin.site.register(OtherFee)