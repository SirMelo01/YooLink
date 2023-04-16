from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
#from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    def items(self):
        return [
            'home',
            'impressum', 'datenschutz', 'cookies', 
            'designtemplates:designtemplates', 'designtemplates:portfolio', 'designtemplates:handwerksbtrieb',
            ]
    
    def location(self, item):
        return reverse(item)