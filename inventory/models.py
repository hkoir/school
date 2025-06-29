from django.db import models
from core.models import Employee
from teachers.models import Teacher
from accounts.models import CustomUser
import uuid





class Warehouse(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True, blank=True,related_name='warehouse_user')
    name = models.CharField(max_length=100)
    warehouse_id = models.CharField(max_length=150, unique=True, null=True, blank=True)  
    address = models.CharField(max_length=255, blank=True, null=True)
    city=models.CharField(max_length=100,null=True,blank=True)
    description = models.TextField(blank=True, null=True)
    reorder_level = models.PositiveIntegerField(default=10,null=True,blank=True)
    lead_time = models.PositiveIntegerField(null=True,blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.warehouse_id:
            self.warehouse_id = f"WH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f" {self.name} "



class Location(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True, blank=True,related_name='location_user')
    location_id = models.CharField(max_length=150, unique=True, null=True, blank=True)     
    warehouse = models.ForeignKey(Warehouse, related_name='locations', on_delete=models.CASCADE)  
    address= models.TextField(null=True,blank=True)  
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.location_id:
            self.location_id = f"LOCID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name





class Supplier(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)
    logo = models.ImageField(upload_to='company_logo/',blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='supplier_user')
    supplier_id = models.CharField(max_length=150, null=True, blank=True)
    contact_person = models.CharField(max_length=255,null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    
    def save(self, *args, **kwargs):
        if not self.supplier_id:
            self.supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='category_user')    
    description = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name




class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True) 
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"





class Inventory(models.Model):
    inventory_id = models.CharField(max_length=30,null=True,blank=True) 
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_user'
    )   
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='warehouse_inventory'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='location_inventory'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_inventories',
        null=True,
        blank=True
    )
    quantity = models.IntegerField(default=0,null=True,blank=True) 
    reorder_level = models.PositiveIntegerField(default=10,null=True,blank=True)
    remarks = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.inventory_id:
            self.inventory_id= f"INVID-{uuid.uuid4().hex[:8].upper()}"
     
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.warehouse}--{self.product.name}--{self.quantity}"




class InventoryTransaction(models.Model):  
    inventory_transaction=models.ForeignKey(Inventory,on_delete=models.CASCADE,null=True, blank=True,related_name='inventory_transaction') 
    transaction_id = models.CharField(max_length=30,null=True,blank=True)    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='inventory_transaction_user')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_inventory_transaction',null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE,null=True, blank=True)
   
    transaction_type = models.CharField(
    max_length=20,
    choices=[
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),       
        ('RETURN', 'RETURN'),   
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
        ('EXISTING_ITEM_IN', 'Existing items'),        
        ('SCRAPPED_OUT', 'Scrapped out'),
        ('SCRAPPED_IN','Scrapped in')
    ],
    null=True, blank=True
    )    
    quantity = models.PositiveIntegerField(null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)       
    remarks = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id= f"INVTID-{uuid.uuid4().hex[:8].upper()}"
     
        super().save(*args, **kwargs)   

    def __str__(self):       
        return f"{self.transaction_id}-{self.transaction_type}-{self.product}-{self.quantity}"


