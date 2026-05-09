from django.urls import path, include
from . import views

from .auth_views import (
    CMSPasswordChangeDoneView,
    CMSPasswordChangeView,
    CMSPasswordResetCompleteView,
    CMSPasswordResetConfirmView,
    CMSPasswordResetDoneView,
    CMSPasswordResetRequestView,
)

app_name = "cms"

urlpatterns = [
    path("", views.cms, name="cms"),
    path("login/", views.Login_Cms, name="login"),
    path("login/2fa/", views.Login_Cms_2FA_Verify, name="login-2fa"),
    path("logout/", views.custom_logout, name="logout"),

    # Images
    path("upload/", views.upload_view, name="upload"),
    path("upload/delete/<str:name>/", views.delete_file_by_name, name="upload-delete"),
    path("upload/post", views.file_upload_view, name="post-upload"),
    path("images/", views.images_view, name="images-view"),
    path("images/delete/<int:id>/", views.delete_file, name="image-delete"),
    path("images/update/<int:id>/", views.update_file, name="image-update"),
    path("images/all/", views.all_images, name="all-images"),

    # FAQ
    path("faq/sort/", views.update_faq_order, name="faq-sort"),
    path("faq/", views.faq_view, name="faq-view"),
    path("faq/update/", views.update_faq, name="faq-update"),
    path("faq/delete/<int:id>/", views.del_faq, name="faq-update"),

    # Blog
    path("blog/", views.blog_view, name="blog-view"),
    path("blog/add/", views.add_blog, name="blog-add"),
    path("blog/create/", views.create_blog, name="blog-create"),
    path("blog/<int:id>/", views.blog_details, name="blog-details"),
    path("blog/<int:id>/getCode/", views.blog_code, name="blog-code"),
    path("blog/<int:id>/delete/", views.delete_blog, name="blog-delete"),
    path("blog/<int:id>/update/", views.update_blog, name="blog-update"),

    # Galery
    path("galerien/", views.galerien, name="galerien"),
    path("galery/images/update/<int:id>/", views.update_galery_image, name="galery-update-img"),
    path("galery/create/", views.create_galery, name="galery-create"),
    path("galery/getImages/", views.get_galery_images, name="galery-get-images"),
    path("galery/delete-img/<int:id>/", views.delete_galery_img, name="delete-galery-img"),
    path("galery/<int:id>/", views.galery_view, name="galery-view"),
    path("galery/<int:id>/upload/", views.upload_galery_img, name="upload-galery-img"),
    path("galery/<int:id>/save/", views.save_galery, name="galery-save"),
    path("galery/<int:id>/delete/", views.delete_galery, name="galery-delete"),
    path("galerien/all/", views.all_galerien, name="all-galerien"),

    # Seiten
    path("seiten/", views.content_view, name="sites"),
    path("seiten/save/", views.saveTextContent, name="save_text_content"),
    path("seiten/hauptseite/", views.site_view_main, name="site_hauptseite"),
    path("seiten/hauptseite/Hero/", views.site_view_main_hero, name="site_hauptseite_hero"),
    path("seiten/hauptseite/Reponsive/", views.site_view_main_responsive, name="site_hauptseite_responsive"),
    path("seiten/hauptseite/CMS/", views.site_view_main_cms, name="site_hauptseite_cms"),
    path("seiten/hauptseite/Preis/", views.site_view_main_price, name="site_hauptseite_price"),
    path("seiten/hauptseite/Team/", views.site_view_main_team, name="site_hauptseite_team"),
    path("seiten/hauptseite/Know-How/", views.site_view_main_know_how, name="site_hauptseite_know_how"),
    path("seiten/hauptseite/Kunden/", views.site_view_main_kunden, name="site_hauptseite_kunden"),
    path("seiten/hauptseite/FAQ/", views.site_view_main_faq, name="site_hauptseite_faq"),
    path("seiten/Kunden/", views.site_view_kunden, name="site_kunden"),
    path("seiten/leistungen/", views.site_view_leistungen, name="site_leistungen"),
    path("seiten/leistungen/cms/", views.site_view_cmsinfo, name="site_leistungen_cms"),
    path("seiten/leistungen/logos/", views.site_view_logos, name="site_leistungen_logos"),
    path("seiten/datenschutz/", views.site_view_datenschutz, name="site_datenschutz"),
    path("seiten/datenschutz/save/", views.save_privacy_policy, name="save_privacy_policy"),

    # Email
    path("email/request/", views.email_send, name="send-email"),

    # Settings
    path("settings/", views.user_settings_view, name="settings-view"),
    path("settings/update/", views.user_settings_update, name="settings-update"),

    path("settings/logo/", views.logo_settings_view, name="logo-settings"),
    path("settings/logo/update/", views.update_logo_favicon, name="logo-update"),
    path("settings/logo/delete/", views.delete_logo_favicon, name="logo-delete"),

    path("settings/security/", views.security_settings_view, name="security-settings"),
    path("settings/security/send-code/", views.send_email_2fa_code, name="security-send-code"),
    path("settings/security/verify-code/", views.verify_email_2fa_code, name="security-verify-code"),
    path("settings/security/disable-2fa/", views.disable_email_2fa, name="security-disable-2fa"),
    path("settings/developer/", views.developer_settings_view, name="developer-settings"),
    path("settings/developer/docs/", views.developer_api_docs_view, name="developer-api-docs"),

    # Opening Hours
    path("openinghours/", views.opening_hours_view, name="openinghours-view"),
    path("openinghours/update/", views.opening_hours_update, name="openinghours-update"),

    # Team Members
    path("team/", views.team_member_list, name="team-list"),
    path("team/create/", views.create_team_member, name="create-team-member"),
    path("team/<int:id>/", views.get_team_member, name="get-team-member"),
    path("team/<int:id>/update/", views.update_team_member, name="update-team-member"),
    path("team/<int:id>/delete/", views.delete_team_member, name="delete-team-member"),
    path("team/reorder/", views.reorder_team_members, name="team-reorder"),

    # Utils
    path("set-language/<str:lang_code>/", views.cms_set_language, name="set-language"),

    # Pricing
    path("pricing/", views.pricing_card_overview, name="pricingcard-list"),
    path("pricing/create/", views.create_pricing_card, name="pricingcard-create"),
    path("pricing/<int:pk>/edit/", views.edit_pricing_card, name="pricingcard-edit"),
    path("pricing/<int:pk>/delete/", views.delete_pricing_card, name="pricingcard-delete"),
    path("pricing/<int:pk>/features/", views.manage_features, name="pricingcard-features"),
    path("pricingcards/reorder/", views.pricingcard_reorder, name="pricingcard-reorder"),

    # Buttons
    path("buttons/", views.button_list, name="button-list"),
    path("buttons/create/", views.button_create, name="button-create"),
    path("buttons/<int:pk>/edit/", views.button_edit, name="button-edit"),
    path("buttons/<int:pk>/delete/", views.button_delete, name="button-delete"),

    # AnyFiles
    path("anyfiles/upload/", views.anyfile_upload_view, name="anyfile-upload"),
    path("anyfiles/", views.anyfile_list_view, name="anyfile-list"),
    path("anyfiles/all/", views.anyfiles_all, name="anyfiles-all"),
    path("anyfiles/uploader/", views.anyfile_uploader, name="anyfile-uploader"),
    path("anyfiles/delete/<int:id>/", views.anyfile_delete_view, name="anyfile-delete"),
    path("anyfiles/update/<int:id>/", views.anyfile_update_view, name="anyfile-update"),
    path("videos/get/<int:pk>/", views.get_video_details, name="get_video_details"),

    # Videos
    path("videos/", views.list_videos, name="list_videos"),
    path("videos/all/", views.list_all_videos, name="cms_videos_all"),
    path("videos/create/", views.create_video, name="create_video"),
    path("videos/edit/<int:pk>/", views.edit_video, name="edit_video"),
    path("videos/delete/<int:pk>/", views.delete_video, name="delete_video"),

    # Files
    path("files/", views.cms_files, name="cms-files"),

    # Notifications
    path("notifications/", views.notifications_list, name="notifications-list"),
    path("notifications/mark-all-read/", views.notifications_mark_all_read, name="notifications-mark-all-read"),
    path("notifications/spam/", views.notifications_spam_list, name="notifications-spam-list"),
    path("notifications/spam/delete-all/", views.notifications_spam_delete_all, name="notifications-spam-delete-all"),
    path("notifications/<int:pk>/mark-spam/", views.notification_mark_spam, name="notification-mark-spam"),
    path("notifications/<int:pk>/mark-ham/", views.notification_mark_ham, name="notification-mark-ham"),
    path("notifications/<int:pk>/mark-read/", views.notification_mark_read, name="notification-mark-read"),
    path("notifications/<int:pk>/", views.notification_detail, name="notification-detail"),
    path("notifications/<int:pk>/delete/", views.notification_delete, name="notification-delete"),

    # Shop CMS
    path("shop/", include("yoolink.ycms.applications.shop.cms_urls")),

    # Auth
    path("account/password/", CMSPasswordChangeView.as_view(), name="password_change"),
    path("account/password/done/", CMSPasswordChangeDoneView.as_view(), name="password_change_done"),

    path("password-reset/", CMSPasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/done/", CMSPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", CMSPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", CMSPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
