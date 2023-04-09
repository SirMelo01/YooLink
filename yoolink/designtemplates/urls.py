from django.urls import path, include
from yoolink.designtemplates.views import load_designtemp

app_name = "designtemplates"
urlpatterns = [
    path("", view=load_designtemp, name="designtemplates"),
]
