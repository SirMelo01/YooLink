from django.urls import path, include
from yoolink.designtemplates.views import load_designtemp
from django.views.generic import TemplateView

app_name = "designtemplates"
urlpatterns = [
    path("", view=load_designtemp, name="designtemplates"),
    path("template1/", TemplateView.as_view(template_name="designs/template1.html"), name="template1"),
]
