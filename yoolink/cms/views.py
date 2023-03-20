from django.shortcuts import render, redirect
from cms.models import Text_Content, Galerie
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

# Create your views here.

@login_required(login_url='login')
def Text_Setting_Content(request):
    print("text")
    text1=Text_Content.objects.get(id=2).text1
    bild = Text_Content.objects.get(id = 2).bild

    
    context = {
            'text1': text1,
            'bild': bild,
            }
    return render(request, 'cms/cms.html', context=context)


@login_required(login_url='login')
def Upload_Content(request):
     # Get all Files in Galerie
     file_list= []
     allfiles = Galerie.objects.all()
     for file in allfiles:
         file_list.append(file.file.url)

     if request.method == 'POST':
        files = request.FILES.getlist('files')
        
        for file in files:
             new_file = Galerie(
                file = file
             )
             new_file.save()
        return render(request, 'cms/cms_upload.html', {'all_urls': file_list})
     else:
        return render(request, 'cms/cms_upload.html', {'all_urls': file_list})


def Login_Cms(request):
    admin = False
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            user_authenticated = user.objects.get(username=user.get_username())
            
            login(request, user)
            return redirect('cms/cms.html')
        else:
            #messages.error(request, "Falsche Anmeldeinformationen. Bitte versuchen Sie es erneut.")
            return redirect('pages/home.html')
       
    return render(request, 'registration/login.html', {
        'currentPath': request.get_full_path
    })