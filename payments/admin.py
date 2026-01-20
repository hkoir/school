from django.contrib import admin
from.models import Payment,FeeStructure,AdmissionFee,AdmissionFeePolicy,PaymentInvoice,AdmissionFeePayment
from .models import TransportPayment,HostelRoomPayment,ExamFeePayment,OtherFeePayment
from.models import TuitionFeePayment


admin.site.register(Payment)
admin.site.register(FeeStructure)

admin.site.register(AdmissionFee)

admin.site.register(AdmissionFeePolicy)
admin.site.register(PaymentInvoice)

admin.site.register(AdmissionFeePayment)
admin.site.register(TuitionFeePayment)


admin.site.register(TransportPayment)
admin.site.register(HostelRoomPayment)
admin.site.register(OtherFeePayment)
admin.site.register(ExamFeePayment)

