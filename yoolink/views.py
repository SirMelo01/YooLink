from django.shortcuts import render
#from yoolink.cms.models import FAQ


def load_index(request):
    #faq = FAQ.objects.all()

    context = {
        'FAQ': [],
    }
    return render(request, 'pages/index.html', context=context)