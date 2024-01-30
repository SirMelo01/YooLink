from django.contrib import admin
from .models import Galerie, UserSettings, GaleryImage, FAQ, Product, fileentry, Blog, Message, TextContent, Order, OrderItem, Review, Brand, Category

# Register your models here.


admin.site.register(Galerie)
admin.site.register(GaleryImage)
admin.site.register(FAQ)
admin.site.register(fileentry)
admin.site.register(Blog)
admin.site.register(Message)
admin.site.register(TextContent)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(UserSettings)