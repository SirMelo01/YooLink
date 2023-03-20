from django.contrib import admin
from . import models




class CmsAdminArea(admin.AdminSite):
    site_header = 'CMS Admin Area'

cms_admin_site = CmsAdminArea(name='CmsAdmin')

cms_admin_site.register(models.Galerie)
cms_admin_site.register(models.fileentry)