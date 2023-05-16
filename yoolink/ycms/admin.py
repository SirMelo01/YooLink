from django.contrib import admin
from .models import Galerie, GaleryImage, FAQ, fileentry, Blog, Message

# Register your models here.


admin.site.register(Galerie)
admin.site.register(GaleryImage)
admin.site.register(FAQ)
admin.site.register(fileentry)
admin.site.register(Blog)
admin.site.register(Message)