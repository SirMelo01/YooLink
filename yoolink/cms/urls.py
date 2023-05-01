from django.urls import path, include
from . import views


app_name = "cms"
urlpatterns = [
    path("", views.upload, name="cms"),
    path("login/", views.Login_Cms, name="login"),
    # Images
    path('upload/', views.upload_view, name='upload'),
    path('upload/delete/<str:name>/', views.delete_file_by_name, name='upload-delete'),
    path('upload/post', views.file_upload_view, name='post-upload'),
    path('images/', views.images_view, name='images-view'),
    path('images/delete/<int:id>/', views.delete_file, name='image-delete'),
    # FAQ
    path('faq/sort/', views.update_faq_order, name='faq-sort'),
    path('faq/', views.faq_view, name='faq-view'),
    path('faq/update/', views.update_faq, name='faq-update'),
    path('faq/delete/<int:id>/', views.del_faq, name='faq-update'),
    # Blog
    path('blog/', views.blog_view, name='blog-view'),
    path('blog/add/', views.add_blog, name='blog-add'),
    path('blog/update/<int:id>/', views.update_blog, name='blog-update'),
    path('blog/delete/<int:id>/', views.delete_blog, name='blog-delete'),
    # Galery
    path('galerien/', views.galerien, name='galerien'),
    path('galery/create/', views.create_galery, name='galery-create'),
    path('galery/<int:id>/', views.galery_view, name='galery-view'),
    path('galery/<int:id>/upload/', views.upload_galery_img, name='upload-galery-img'),
    path('galery/<int:id>/save/', views.save_galery, name='galery-save'),
    path('galery/delete-img/<int:id>/', views.delete_galery_img, name='delete-galery-img'),
    path('galery/<int:id>/delete/', views.delete_galery, name='galery-delete'),
]
