from django.urls import path

from . import views


urlpatterns = [
    path("", views.content_view, name="sites"),
    path("save/", views.save_text_content, name="save_text_content"),
    path("hauptseite/", views.site_view_main, name="site_hauptseite"),
    path("hauptseite/Hero/", views.site_view_main_hero, name="site_hauptseite_hero"),
    path("hauptseite/Reponsive/", views.site_view_main_responsive, name="site_hauptseite_responsive"),
    path("hauptseite/CMS/", views.site_view_main_cms, name="site_hauptseite_cms"),
    path("hauptseite/Preis/", views.site_view_main_price, name="site_hauptseite_price"),
    path("hauptseite/Team/", views.site_view_main_team, name="site_hauptseite_team"),
    path("hauptseite/Know-How/", views.site_view_main_know_how, name="site_hauptseite_know_how"),
    path("hauptseite/kunden/", views.site_view_main_kunden, name="site_hauptseite_kunden"),
    path("hauptseite/FAQ/", views.site_view_main_faq, name="site_hauptseite_faq"),
    path("kunden/", views.site_view_kunden, name="site_kunden"),
    path("kunden/customers/", views.customer_list_view, name="customer-list"),
    path("kunden/customers/create/", views.customer_create_view, name="customer-create"),
    path("kunden/customers/reorder/", views.customer_reorder_view, name="customer-reorder"),
    path("kunden/customers/<int:pk>/edit/", views.customer_edit_view, name="customer-edit"),
    path("kunden/customers/<int:pk>/delete/", views.customer_delete_view, name="customer-delete"),
    path("leistungen/", views.site_view_leistungen, name="site_leistungen"),
    path("leistungen/cms/", views.site_view_cmsinfo, name="site_leistungen_cms"),
    path("leistungen/logos/", views.site_view_logos, name="site_leistungen_logos"),
    path("leistungen/visitenkarte/", views.site_view_visitenkarte, name="site_leistungen_visitenkarte"),
    path("datenschutz/", views.site_view_datenschutz, name="site_datenschutz"),
    path("datenschutz/save/", views.save_privacy_policy, name="save_privacy_policy"),
]

