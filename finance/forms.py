
from django import forms
from .models import Expense,PurchasePayment,Asset,PurchaseItem,PurchaseOrder
from django.forms import inlineformset_factory


class AssetForm(forms.ModelForm):
     class Meta:
        model = Asset
        exclude = ['asset_code','user','current_value','last_depreciation_date']
        widgets={
            'purchase_date':forms.DateInput(attrs={
                'type':'date'
            })
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description', 'employee', 'inventory_purchase']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }




class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'reference','vat_ait_policy']


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'description', 'quantity', 'unit_price','purchase_type','batch_no','manufacturing_date','expire_date']
        widgets={
            'manufacturing_date': forms.DateInput(attrs={'type':'date'}),
            'expire_date': forms.DateInput(attrs={'type':'date'})
        }

PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,
    can_delete=True
)

class PurchaseOrderApprovalForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['approval_status']


class PurchasePaymentForm(forms.ModelForm):
    class Meta:
        model = PurchasePayment
        fields = ['amount_paid','method','purchase_type','reference','tax_policy']
