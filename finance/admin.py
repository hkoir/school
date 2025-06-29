from django.contrib import admin
from.models import Expense,SalaryPayment,Asset,AssetDepreciationRecord,Shareholders,ShareholderInvestment


admin.site.register(Expense)
admin.site.register(SalaryPayment) 
admin.site.register(Asset) 
admin.site.register(AssetDepreciationRecord) 

admin.site.register(Shareholders) 
admin.site.register(ShareholderInvestment) 
