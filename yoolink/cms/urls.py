from django.urls import path
from yoolink.cms.views import Text_Setting_Content

app_name = "cms"
urlpatterns = [
    path("", view=Text_Setting_Content, name="redirect"),
]
