from django.urls import path, include
from yoolink.designtemplates.views import load_designtemp
from django.views.generic import TemplateView

app_name = "designtemplates"
urlpatterns = [
    path("", view=load_designtemp, name="designtemplates"),
    path("portfolio/", TemplateView.as_view(template_name="designs/portfolio.html"), name="portfolio"),
    path("handwerksbetrieb/", TemplateView.as_view(template_name="designs/handwerksbetrieb.html"), name="handwerksbtrieb"),
    
]


