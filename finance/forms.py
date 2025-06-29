from.models import Asset
from django import forms
from finance.models import Expense



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
