from django.urls import path, include
from yoolink.cms.views import upload, Login_Cms

app_name = "cms"
urlpatterns = [
    #path("", view=Text_Setting_Content, name="cms"),
    path("upload/", view=upload, name="cmsupload"),
    path("login/", view=Login_Cms, name="login"),
]
