from django.urls import path, include
from yoolink.cms.views import upload, Login_Cms

app_name = "cms"
urlpatterns = [
    path("", view=upload, name="cms"),
    path("login/", view=Login_Cms, name="login"),
]
