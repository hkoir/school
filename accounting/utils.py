from decimal import Decimal
from datetime import date
from accounting.models import JournalEntry, JournalEntryLine, FiscalYear, Account

def create_journal_entry_for_purchase(purchase_payment, description="", vat_amount=0, ait_amount=0, created_by=None):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    total_amount = Decimal(purchase_payment.total_amount)
    vat_amount = Decimal(vat_amount or 0)
    ait_amount = Decimal(ait_amount or 0)
    net_payable = total_amount + vat_amount - ait_amount

    # Create journal entry
    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description or f"Purchase entry for {purchase_payment.purchase_invoice.purchase_shipment.purchase_order.supplier.name}",
        reference=f"PUR-{purchase_payment.id}",
        created_by=created_by
    )

    # Get accounts
    try:
        expense_account = Account.objects.get(code="5200")      # Operating Expenses
        inventory_account = Account.objects.get(code="1150")    # Inventory
        cash_account = Account.objects.get(code="1110")         # Cash
        accounts_payable = Account.objects.get(code="2111")     # Accounts Payable - Trade
        input_vat = Account.objects.get(code="1180")            # Input VAT Recoverable
        ait_payable = Account.objects.get(code="2132")          # AIT Payable
    except Account.DoesNotExist as e:
        raise ValueError(f"Missing required account: {e}")

    # Determine debit account (Inventory or Expense)
    purchase_account = inventory_account if purchase_payment.purchase_invoice.purchase_shipment.purchase_order.is_inventory else expense_account

    # Debit: Purchase amount
    JournalEntryLine.objects.create(
        entry=entry,
        account=purchase_account,
        description="Goods/Services purchased",
        debit=total_amount,
        credit=0
    )

    # Debit: Input VAT (if any)
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=input_vat,
            description="Input VAT Recoverable",
            debit=vat_amount,
            credit=0
        )

    # Credit: AIT Payable (if any)
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_payable,
            description="AIT deducted at source",
            debit=0,
            credit=ait_amount
        )

    # Credit: Payment account (Cash/Bank) or Accounts Payable
    if purchase_payment.payment_method == "CASH":
        payment_account = cash_account
    elif purchase_payment.payment_method == "BANK" and purchase_payment.bank_account:
        # Use bank account as payment account
        payment_account, _ = Account.objects.get_or_create(
            code=f"BANK-{purchase_payment.bank_account.id}",
            defaults={'name': purchase_payment.bank_account.name, 'type': 'ASSET'}
        )
    else:
        payment_account = accounts_payable

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description="Payment made or payable",
        debit=0,
        credit=net_payable
    )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry



def create_journal_entry_for_sales(sale_payment, description="", vat_amount=0, ait_amount=0, created_by=None):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    total_amount = Decimal(sale_payment.total_amount)
    vat_amount = Decimal(vat_amount or 0)
    ait_amount = Decimal(ait_amount or 0)
    net_receivable = total_amount + vat_amount - ait_amount

    # Create journal entry
    entry = JournalEntry.objects.create(
        date=date.today(),
        fiscal_year=fiscal_year,
        description=description or f"Sales entry for {sale_payment.sale_invoice.sale_shipment.sales_order.customer}",
        reference=f"SALE-{sale_payment.id}",
        created_by=created_by
    )

    # Get accounts
    try:
        sales_revenue = Account.objects.get(code="4100")       # Sales Revenue
        output_vat = Account.objects.get(code="2131")          # Output VAT Payable
        cash_account = Account.objects.get(code="1110")        # Cash
        accounts_receivable = Account.objects.get(code="1140") # Accounts Receivable
        ait_receivable = Account.objects.get(code="1190")      # AIT Receivable
        cost_of_goods_sold = Account.objects.get(code="5100")  # COGS
        inventory_account = Account.objects.get(code="1150")   # Inventory
    except Account.DoesNotExist as e:
        raise ValueError(f"Missing required account: {e}")

    # Debit: Cash/Bank or Accounts Receivable
    if sale_payment.payment_method == "CASH":
        payment_account = cash_account
        
    elif sale_payment.payment_method == "BANK" and sale_payment.bank_account:
        payment_account, _ = Account.objects.get_or_create(
            code=f"BANK-{sale_payment.bank_account.id}",
            defaults={'name': sale_payment.bank_account.name, 'type': 'ASSET'}
        )
    else:  # Credit Sale
        payment_account = accounts_receivable

    JournalEntryLine.objects.create(
        entry=entry,
        account=payment_account,
        description="Sales proceeds (net of AIT)",
        debit=net_receivable,
        credit=0
    )

    # Debit: AIT Recoverable
    if ait_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=ait_receivable,
            description="AIT Recoverable",
            debit=ait_amount,
            credit=0
        )

    # Credit: Sales Revenue
    JournalEntryLine.objects.create(
        entry=entry,
        account=sales_revenue,
        description="Sales revenue recognized",
        debit=0,
        credit=total_amount
    )

    # Credit: Output VAT
    if vat_amount > 0:
        JournalEntryLine.objects.create(
            entry=entry,
            account=output_vat,
            description="Output VAT Payable",
            debit=0,
            credit=vat_amount
        )

    # For GOODS sale: record COGS and reduce inventory
    if sale_payment.sale_invoice.sale_shipment.sales_order.sale_type == "GOODS" and sale_payment.sale_invoice.sale_shipment.sales_order.cost_of_goods_sold:
        cogs = Decimal(sale_payment.sale_invoice.sale_shipment.sales_order.cost_of_goods_sold)
        JournalEntryLine.objects.create(
            entry=entry,
            account=cost_of_goods_sold,
            description="Cost of Goods Sold",
            debit=cogs,
            credit=0
        )
        JournalEntryLine.objects.create(
            entry=entry,
            account=inventory_account,
            description="Reduce inventory for sold goods",
            debit=0,
            credit=cogs
        )

    if not entry.is_balanced():
        raise ValueError(f"Journal entry {entry.id} is not balanced!")

    return entry


""" 

class BankAccount(models.Model):
    name = models.CharField(max_length=100)        # e.g., Bank A - Checking
    code = models.CharField(max_length=20, unique=True)  # optional, for accounting code
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_type = models.CharField(max_length=50, choices=[("CASH", "Cash"), ("BANK", "Bank")])
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} ({self.account_number})"


class Sale(models.Model):
    SALE_TYPES = [
        ("GOODS", "Goods"),
        ("SERVICE", "Service"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sale_type = models.CharField(max_length=20, choices=SALE_TYPES, default="GOODS")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[("CASH","Cash"),("BANK","Bank"),("CREDIT","Credit")])
    bank_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    cost_of_goods_sold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale #{self.id} ({self.sale_type})"






class Purchase(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[("CASH","Cash"),("BANK","Bank"),("CREDIT","Credit")])
    bank_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True)
    is_inventory = models.BooleanField(default=True)  # for inventory vs expense
    created_at = models.DateTimeField(auto_now_add=True)

    

"""