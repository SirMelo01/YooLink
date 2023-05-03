from django.shortcuts import render
from yoolink.ycms.models import FAQ


def load_index(request):
    faq = FAQ.objects.all()

    context = {
        'FAQ': faq,
    }
    return render(request, 'pages/index.html', context=context)