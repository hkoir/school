from django.contrib import admin

from.models import Warehouse,Location,Category,Product,Inventory,InventoryTransaction


admin.site.register(Warehouse)
admin.site.register(Location)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(InventoryTransaction)




