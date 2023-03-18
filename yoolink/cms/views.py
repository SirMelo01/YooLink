from django.shortcuts import render
from cms.models import Text_Content

# Create your views here.


def Text_Setting_Content(request):
    print("text")
    text1=Text_Content.objects.get(id=1).text1
    
    context = {
            'text1': text1,
            }
    return render(request, 'admin/cms.html', context=context)