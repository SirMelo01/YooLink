from django.contrib import admin

from .models import PrivacyPolicy, TextContent


admin.site.register(TextContent)
admin.site.register(PrivacyPolicy)

