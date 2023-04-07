from django.shortcuts import render, redirect
from yoolink.cms.models import Text_Content, Galerie, fileentry, FAQ
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .forms import fileform







def load_index(request):
    faq = FAQ.objects.all().values().order_by('id')

    context = {
        'FAQ': faq,
    }
    return render(request, 'pages/home.html', context=context)



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

        
        # Set the file path for the source image
        #path = r'../../var/lib/docker/volumes/yoolink_production_django_media/_data/media/6.jpg'

        # Set the directory for saving the image
        #directory = r'yoolink/media'

        # Load the image using OpenCV
        #img = cv2.imread(path)

        # Change the working directory to the specified directory for saving the image
        #os.chdir(directory)

        # Save the image with the filename "cat.jpg"
        #filename = '6.jpg'
        #cv2.imwrite(filename, img) 
        
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