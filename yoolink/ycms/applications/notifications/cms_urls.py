from django.urls import path

from . import views


urlpatterns = [
    path("", views.notifications_list, name="notifications-list"),
    path("mark-all-read/", views.notifications_mark_all_read, name="notifications-mark-all-read"),
    path("spam/", views.notifications_spam_list, name="notifications-spam-list"),
    path("spam/delete-all/", views.notifications_spam_delete_all, name="notifications-spam-delete-all"),
    path("<int:pk>/mark-spam/", views.notification_mark_spam, name="notification-mark-spam"),
    path("<int:pk>/mark-ham/", views.notification_mark_ham, name="notification-mark-ham"),
    path("<int:pk>/mark-read/", views.notification_mark_read, name="notification-mark-read"),
    path("<int:pk>/", views.notification_detail, name="notification-detail"),
    path("<int:pk>/delete/", views.notification_delete, name="notification-delete"),
]

