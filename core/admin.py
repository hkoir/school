from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Company,Location,Employee,Notice,EmployeeRecordChange,MonthlySalaryReport
from.models import SalaryIncrementAndPromotion,CompanyPolicy,SalaryStructure,Position,Employeelevel,JobDescription,JobRequirement

from.models import Doctor,Nurse,Specialization,TaxPolicy,ServiceTaxPolicy

admin.site.register(TaxPolicy)
admin.site.register(ServiceTaxPolicy)
admin.site.register(Company)
admin.site.register(Location)
admin.site.register(Employeelevel)
admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(Notice)

admin.site.register(EmployeeRecordChange)

admin.site.register(MonthlySalaryReport)
admin.site.register(SalaryIncrementAndPromotion)

admin.site.register(CompanyPolicy)
admin.site.register(SalaryStructure)


admin.site.register(JobRequirement)
admin.site.register(JobDescription)

admin.site.register(Doctor)
admin.site.register(Nurse)
admin.site.register(Specialization)
