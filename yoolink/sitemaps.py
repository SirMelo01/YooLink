from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from django.utils import timezone
from yoolink.ycms.models import Blog
#from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    def items(self):
        return [
            'home',
            'impressum', 'datenschutz', 'cookies', 
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
          return Blog.objects.filter(active=True)
     
     def lastmod(self, obj):
          return obj.last_updated