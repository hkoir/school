from django.db import models
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from accounts.models import CustomUser




class Shareholders(models.Model):
    name = models.CharField(max_length=100)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g. 25.00 for 25%")

    def __str__(self):
        return f"{self.name} - {self.ownership_percentage}%"


class ShareholderInvestment(models.Model):
    share_holder = models.ForeignKey(Shareholders,on_delete=models.CASCADE,null=True,blank=True,related_name='shareholders')
    investor_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date_invested = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.investor_name} - ৳{self.amount}"



class Asset(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    asset_code = models.CharField(max_length=30, unique=True, blank=True)
    name = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=20, decimal_places=2)   
    purchase_date = models.DateField(null=True, blank=True)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # % per year
    current_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    last_depreciation_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):       
        if not self.asset_code:
            year = self.purchase_date.year if self.purchase_date else timezone.now().year
            count = Asset.objects.filter(purchase_date__year=year).count() + 1
            self.asset_code = f"AS{str(year)[-2:]}{count:06d}"

        if self.pk:
            previous = Asset.objects.get(pk=self.pk)
            if self.value != previous.value:
                self.current_value = self.value
        else:
            self.current_value = self.value

        super().save(*args, **kwargs)



    def apply_asset_depreciation(self):
        today = timezone.now().date()
        # Apply if last_depreciation_date is None (never depreciated)
        if self.last_depreciation_date is None or self.last_depreciation_date < today - relativedelta(months=1):
            if self.depreciation_rate:
                rate = self.depreciation_rate / Decimal('100.0')
                depreciation_amount = self.current_value * rate

                previous_value = self.current_value
                self.current_value -= depreciation_amount
                self.last_depreciation_date = today

                # Create expense record
                Expense.objects.create(
                    user=self.user,
                    category="DEPRECIATION",
                    amount=depreciation_amount,
                     date=today, 
                     description="Automated asset depreciation"
                )

                # Save depreciation record
                AssetDepreciationRecord.objects.create(
                    asset=self,
                    depreciation_amount=depreciation_amount,
                    previous_value=previous_value,
                    new_value=self.current_value,
                    notes="Automated monthly depreciation"
                )

                self.save()
                return depreciation_amount
            else:
                return None  # No depreciation rate set
        else:
            return None  # Already depreciated this month



    def __str__(self):
        return f"{self.asset_code} - {self.name}"
    


    
class AssetDepreciationRecord(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_records')
    depreciation_amount = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    previous_value = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    new_value = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.created_at} - Depreciation: {self.depreciation_amount}"


from inventory.models import Inventory,InventoryTransaction
from core.models import Employee

class Expense(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    EXPENSE_CATEGORIES = [
        ('SALARY', 'Salary'),
        ('INVENTORY', 'Inventory Purchase'),
        ('UTILITY', 'Utility Bills'),
        ('DEPRECIATION', 'Asset Depreciation'),
        ('OTHER', 'Other Expense'),
    ]
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES,blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)  
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)     
    inventory_purchase = models.ForeignKey(InventoryTransaction, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-date']



class SalaryPayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField(help_text="Use the first day of the month (e.g., 2025-06-01)")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_on = models.DateField(auto_now_add=True)
    is_posted_to_expense = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.employee.name} - {self.month.strftime('%B %Y')}"

