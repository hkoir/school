from django.contrib import admin
from.models import AcademicSession,Faculty,Department,AcademicLevel,Program,Term,Subject,SubjectOffering
from.models import VarsityStudentEnrollment,StudentSubjectEnrollment,StudentSubjectResult,StudentCGPA
from.models import StudentTermRegistration,StudentTermResult,LanguageVersion
from.models import AdmissionFee,AdmissionFeePolicy,UniversityFeeStructure,ClassRoom,Exam,ExamSchedule,ExamRegistration
from.models import SubjectAssignment,UniversityTermInvoice,UniversityPayment,ClassSchedule


admin.site.register(AcademicSession)
admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(AcademicLevel)

admin.site.register(Program)
admin.site.register(Term)
admin.site.register(Subject)
admin.site.register(SubjectOffering)


admin.site.register(VarsityStudentEnrollment)
admin.site.register(StudentSubjectEnrollment)
admin.site.register(StudentSubjectResult)
admin.site.register(StudentCGPA)


admin.site.register(StudentTermRegistration)
admin.site.register(StudentTermResult)
admin.site.register(LanguageVersion)
admin.site.register(AdmissionFee)


admin.site.register(AdmissionFeePolicy)
admin.site.register(UniversityFeeStructure)
admin.site.register(ClassRoom)
admin.site.register(ClassSchedule)
admin.site.register(Exam)


admin.site.register(ExamSchedule)
admin.site.register(ExamRegistration)
admin.site.register(SubjectAssignment)
admin.site.register(UniversityTermInvoice)
admin.site.register(UniversityPayment)
