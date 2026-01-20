from django.db import models
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from core.models import Employee
from accounts.models import CustomUser

from inventory.models import Supplier,Product
from core.models import TaxPolicy
from django.db.models import Sum

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
        if self.last_depreciation_date is None or self.last_depreciation_date < today - relativedelta(months=1):
            if self.depreciation_rate:
                rate = self.depreciation_rate / Decimal('100.0')
                depreciation_amount = self.current_value * rate

                previous_value = self.current_value
                self.current_value -= depreciation_amount
                self.last_depreciation_date = today

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
    inventory_purchase = models.ForeignKey('inventory.InventoryTransaction', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-date']


class PurchaseOrder(models.Model):
    vendor = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=50, blank=True, null=True)  
    vat_ait_policy = models.ForeignKey(TaxPolicy,on_delete=models.CASCADE,related_name='purchase_vat_policies', blank=True, null=True)    
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ait_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    total_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approval_status = models.CharField(max_length=30, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('received', 'Received'),
        ('billed', 'Billed'),
        ('closed', 'Closed'),
    ], default='pending')

    date_approved = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def total_paid(self):
        return sum(p.amount_paid for p in self.purchase_payments.all())

    @property
    def balance_due(self):
        return self.total_payable - self.total_paid
    
    def save(self, *args, **kwargs):       
        super().save(*args, **kwargs)      
        policy = self.vat_ait_policy
        base = sum((item.total for item in self.purchase_items.all()), Decimal('0.00'))
        vat_amount = Decimal('0.00')
        ait_amount = Decimal('0.00')

        if policy:
            vat_rate = policy.vat_rate / Decimal('100')
            ait_rate = policy.ait_rate / Decimal('100')

            vat_amount = base * vat_rate if policy.vat_type == "exclusive" else base * vat_rate / (1 + vat_rate)
            ait_amount = base * ait_rate if policy.ait_type == "exclusive" else base * ait_rate / (1 + ait_rate)

        self.subtotal = base
        self.vat_amount = vat_amount
        self.ait_amount = ait_amount
        self.total_payable = base + vat_amount - ait_amount       
        super().save(update_fields=["subtotal", "vat_amount", "ait_amount", "total_payable"])



    def __str__(self):
        return f"PO-{self.id} ({self.vendor})"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='purchase_items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=15,decimal_places=2,null=True,blank=True)
    PURCHASE_TYPE = [
        ('inventory', 'Inventory Item'),
        ('asset', 'Fixed Asset'),
        ('expense', 'Expense (Non-Inventory)'),
    ]
    purchase_type = models.CharField(max_length=20, choices=PURCHASE_TYPE, default='inventory', blank=True, null=True,)
    batch_no = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_date = models.DateField(null=True,blank=True)
    expire_date = models.DateField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):  
        if not self.subtotal:
            self.subtotal = self.unit_price * self.quantity            
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.product} x {self.quantity}"
   


class PurchasePayment(models.Model):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="purchase_payments")
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)    
    tax_policy = models.ForeignKey(TaxPolicy,on_delete=models.CASCADE,related_name='purchase_payment_tax_policies', blank=True, null=True)    
    method = models.CharField(max_length=30, choices=[
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('MFS', 'Mobile Financial Service')
    ])

    PURCHASE_TYPE = [
        ('inventory', 'Inventory Item'),
        ('asset', 'Fixed Asset'),
        ('expense', 'Expense (Non-Inventory)'),
    ]
    purchase_type = models.CharField(max_length=30, choices=PURCHASE_TYPE,blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Purchase {self.purchase.id}"




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

