from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from django.utils import timezone
from yoolink.ycms.models import Blog, Product
#from django.urls import reverse
from django.utils.translation import get_language

class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    def items(self):
        return [
            'home',
            'impressum', 'datenschutz', 'cookies', 
            'kunden', 'kontakt', 'skills', 'ycmsinfo',
            'designtemplates:designtemplates', 'designtemplates:portfolio', 'designtemplates:handwerksbtrieb',
            'blog:blog'
            ]
    
    def lastmod(self, item):
            return timezone.now()
    
    def location(self, item):
        return reverse(item)
    
class BlogSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        lang = get_language() or 'de'
        return Blog.objects.filter(active=True, language=lang)

    def lastmod(self, obj):
        return obj.last_updated
     
class ProductSitemap(Sitemap):
     changefreq = "weekly"
     def items(self):
          return Product.objects.filter(is_active=True)
     
     def lastmod(self, obj):
          return obj.updated_at