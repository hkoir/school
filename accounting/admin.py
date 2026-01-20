from django.contrib import admin
from.models import JournalEntry,JournalEntryLine,FiscalYear,Account

admin.site.register(Account)
admin.site.register(FiscalYear)
admin.site.register(JournalEntry)
admin.site.register(JournalEntryLine)
