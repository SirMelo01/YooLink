from django.urls import path, include
from yoolink.cms.views import upload, Login_Cms, upload_view, file_upload_view


app_name = "cms"
urlpatterns = [
    path("", view=upload, name="cms"),
    path("login/", view=Login_Cms, name="login"),
        path('upload/', view=upload_view, name='upload'),
    path('upload/post', view=file_upload_view, name='post-upload'),
    #path('images/', views.images_view, name='images-view'),
]
