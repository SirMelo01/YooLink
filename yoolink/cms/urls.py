from django.urls import path, include
from yoolink.cms.views import Text_Setting_Content, Upload_Content, Login_Cms

app_name = "cms"
urlpatterns = [
    path("", view=Text_Setting_Content, name="cms"),
    path("upload/", view=Upload_Content, name="cmsupload"),
    path("login/", view=Login_Cms, name="login"),
]
