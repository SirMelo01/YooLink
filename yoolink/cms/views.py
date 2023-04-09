from django.shortcuts import render, redirect
from yoolink.cms.models import Text_Content, Galerie, fileentry, FAQ
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .forms import fileform
from django.conf import settings


## gehört noch verschoben in dei views auserhalb der cms app, da dies für das laden der Index seite zusändig ist und nichts mit dem cms zu tun hat.
def load_index(request):
    faq = FAQ.objects.all().values().order_by('id')

    context = {
        'FAQ': faq,
    }
    return render(request, 'pages/home.html', context=context)
## gehört noch verschoben in dei views auserhalb der cms app, da dies für das laden der Index seite zusändig ist und nichts mit dem cms zu tun hat.


@login_required(login_url='login')
def upload(request):

    context = {'form': None, 'last': None}

    if request.method == 'POST':
        form = fileform(request.POST, request.FILES)
        if form.is_valid():
            context['last'] = '\n'.join([f.name for f in request.FILES.getlist('file')])
            
            for file in request.FILES.getlist('file'):
                new_file = fileentry(
                    file = file
                )
                new_file.save()

    else:
        form = fileform()

    context['form'] = form
    return render(request, 'pages/cms.html', context)



def Login_Cms(request):
    admin = False
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            user_authenticated = user.objects.get(username=user.get_username())
            
            login(request, user)
            return redirect('pages/cms.html')
        else:
            #messages.error(request, "Falsche Anmeldeinformationen. Bitte versuchen Sie es erneut.")
            return redirect('pages/home.html')
       
    return render(request, 'registration/login.html', {
        'currentPath': request.get_full_path
    })