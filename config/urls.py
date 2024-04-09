from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from yoolink.views import load_index, kontaktform, shop, detail
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path, include

from django.contrib.sitemaps.views import sitemap
from yoolink.sitemaps import StaticViewSitemap, BlogSitemap, ProductSitemap

from yoolink.ycms.views import cart_verify_success_view, cart_view, order_verify_success_view, order_verify_view

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'product': ProductSitemap,
}

urlpatterns = [
    path("", view=load_index, name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Your stuff: custom urls includes go here
    path("", include('django.contrib.auth.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name="django.contrib.sitemaps.views.sitemap",),
    path("impressum/", TemplateView.as_view(template_name="pages/impressum.html"), name="impressum"),
    path("kontakt/", view=kontaktform, name="kontakt"),
    path("datenschutz/", TemplateView.as_view(template_name="pages/datenschutz.html"), name="datenschutz"),
    path("cookies/", TemplateView.as_view(template_name="pages/cookies.html"), name="cookies"),
    path("cms/", include("yoolink.ycms.urls", namespace="ycms")),
    path("vorlagen/", include("yoolink.designtemplates.urls", namespace="designtemplates")),
    path("blog/", include("yoolink.blog.urls", namespace="blog")),

    # Shop urls
    path("products/", view=shop, name="products"),
    path("products/<int:product_id>-<slug:slug>/", view=detail, name="product-detail"),

    path('cart/', cart_view, name='cart-view'),
    path('cart/success/', cart_verify_success_view, name='cart-verify-success-view'),

    path('order/verify/', order_verify_view, name='order-verify'),
    path('order/success/', order_verify_success_view, name='order-verify-success-view'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
