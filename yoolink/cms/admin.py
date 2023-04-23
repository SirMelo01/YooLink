from django.contrib import admin

from .models import fileentry, FAQ, Blog



admin.site.register(fileentry)
admin.site.register(Blog)
admin.site.register(FAQ)

# Register your models here.
