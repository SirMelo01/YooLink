from django.shortcuts import get_object_or_404, render, redirect
from yoolink.cms.models import Text_Content, Galerie, fileentry, FAQ
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponse
from .forms import fileform
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


def resize_image(image):
    
    img = Image.open(image)
    format = img.format
    img = img.resize((int(img.width), int(img.height)), resample=Image.LANCZOS)
    img.info['dpi'] = (72,72)

    buffer = BytesIO()

    img.save(buffer, format=format)

    file = InMemoryUploadedFile(
        buffer,
        None,
        f"{image.name.split('.')[0]}.{format.lower()}",
        "image/{format.lower()}",
        buffer.getbuffer().nbytes,
        None
    )
    return file

def scale_image(image):
    img = Image.open(image)
    format = img.format
    img.thumbnail((1920,1920), Image.ANTIALIAS)
    buffer = BytesIO()

    img.save(buffer, format=format, quality=100)
    buffer.seek(0)

    file = InMemoryUploadedFile(
        buffer,
        None,
        f"{image.name.split('.')[0]}.{format.lower()}",
        f"image/{format.lower()}",
        buffer.tell(),
        None
    )

    return file



def compress_image(image):
    img = Image.open(image)
    buffer = BytesIO()

    target_size = 500 * 1024 # 500 KB
    quality = 95
    format = img.format
    img.save(buffer, format=format, quality=quality)
    while buffer.tell() > target_size and quality > 5:
        buffer.seek(0)
        buffer.truncate()
        quality -= 5

        img.save(buffer, format=format, quality=quality)

    file = InMemoryUploadedFile(
        buffer,
        None,
        f"{image.name.split('.')[0]}.{format.lower()}",
        f"image/{format.lower()}",
        buffer.tell(),
        None
    )

    return file




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








# --------------- [FILES] ---------------
# Displays Document Upload Page
@login_required(login_url='login')
def upload_view(request):


    data = {
        
    }
    return render(request, "pages/upload.html", data)

# Uploads File (used by dropzone.js)
@login_required(login_url='login')
def file_upload_view(request):
    if request.method == 'POST':
        my_file = request.FILES.get('file')

# für mich zum merken: Bild soll:
#           1. scaled_image auf 1920 breite
#           2. resized_image auf dpi von (72,72)
#           3. compressed_image auf maximal 200KB - 500KB Internet ist sich noch nicht einig (falls die Datei zu gross ist)

# Alles klappt bis jetzt, jedoch bloed mit dem inmemoryspeicher geloest. Vielleicht in eine Methode aber dann ist
# trotzdem ein mal inmemory da... kann man das clearen? 

# aus der anleitung von oben die drei schritte soll in eine Methode 

        # Resize the image
        #resized_image = resize_image(my_file)

        # Compress the image
        #compressed_image = compress_image(resized_image)

        scaled_image = scale_image(my_file)

        fileentry.objects.create(file=scaled_image)
        return HttpResponse('')
    return JsonResponse({'post': 'false'})

# Delete File
@login_required(login_url='login')
def delete_file(request, id):
    file = fileentry.objects.get(id=id)
    file.delete()
    return JsonResponse({"success": "File wurde erfolgreich gelöscht"})

# Displays all your uploaded images
@login_required(login_url='login')
def images_view(request):
    files = fileentry.objects.all()
    return render(request, "pages/cms/images.html", {"files": files})

# --------------- [FAQ] ---------------
@login_required(login_url='login')
def faq_view(request):
    data = {
        "faqs":  FAQ.objects.all()
    }
    return render(request, "pages/cms/faq.html", data)

# Update or create FAQ
@login_required(login_url='login')
def update_faq(request):
    # Update specific FAQ
    if request.method == 'POST':
        faq_id = request.POST.get('faq_id')
        faq = FAQ.objects.get(id=faq_id)
        faq.question = request.POST.get('question')
        faq.answer = request.POST.get('answer')
        faq.save()
        return JsonResponse({'success': True})
    # Create new FAQ
    elif request.method == 'GET':
        new_question = request.GET.get('question')
        new_answer = request.GET.get('answer')
        faq = FAQ(question=new_question, answer=new_answer)
        faq.save()
        return JsonResponse({'id': faq.id, 'question': faq.question, 'answer': faq.answer, 'order': faq.order, 'success': True})
    
    return JsonResponse({'success': False})

# Delete FAQ
@login_required(login_url='login')
def del_faq(request, id):
    if request.method == 'POST':
        instance = get_object_or_404(FAQ, id=id)
        instance.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Update the FAQ order
@login_required(login_url='login')
def update_faq_order(request):
    if request.method == 'POST':
        faq_ids = request.POST.getlist('faq_ids[]')
        for i, faq_id in enumerate(faq_ids):
            faq = FAQ.objects.get(id=faq_id)
            faq.order = i + 1
            faq.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})