from django.shortcuts import render
from yoolink.cms.models import FAQ


def load_index(request):
    faq = FAQ.objects.all().values().order_by('id')

    context = {
        'FAQ': faq,
    }
    return render(request, 'pages/home.html', context=context)