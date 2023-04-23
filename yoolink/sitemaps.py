from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from django.utils import timezone
#from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    def items(self):
        return [
            'home',
            'impressum', 'datenschutz', 'cookies', 
            'designtemplates:designtemplates', 'designtemplates:portfolio', 'designtemplates:handwerksbtrieb',
            ]
    
    def lastmod(self, item):
            return timezone.now()
    
    def location(self, item):
        return reverse(item)