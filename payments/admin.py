from django.contrib import admin
from.models import Payment,FeeStructure,AdmissionFee,AdmissionFeePolicy,AdmissionFeePayment


admin.site.register(Payment)
admin.site.register(FeeStructure)
admin.site.register(AdmissionFee)
admin.site.register(AdmissionFeePolicy)
admin.site.register(AdmissionFeePayment)
