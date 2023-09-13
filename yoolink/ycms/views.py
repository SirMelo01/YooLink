import json
from django.shortcuts import get_object_or_404, render, redirect
from yoolink.ycms.models import fileentry, FAQ, Galerie, Blog, GaleryImage, TextContent
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from .forms import fileform, Blogform
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile



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

    data = {
        "faq_count":  FAQ.objects.count(),
        "file_count":  fileentry.objects.count(),
        "galery_count":  Galerie.objects.count(),
        "blog_count": Blog.objects.count(),
        'form': form
    }
    return render(request, 'pages/cms/cms.html', data)

# Custom Logout function
def custom_logout(request):
    logout(request)
    return redirect('home')

def Login_Cms(request):
    admin = False
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            user_authenticated = user.objects.get(username=user.get_username())
            
            login(request, user)
            return redirect('pages/cms/cms.html')
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
    return render(request, "pages/cms/upload.html", data)

# Uploads File (used by dropzone.js)
@login_required(login_url='login')
def file_upload_view(request):
    if request.method == 'POST':
        my_file = request.FILES.get('file')

        resized_image = resize_image(my_file)
        scaled_image = scale_image(resized_image)
        compressed_image = compress_image(scaled_image)

        fileentry.objects.create(file=compressed_image)
        return HttpResponse('')
    return JsonResponse({'post': 'false'})

# Delete File
@login_required(login_url='login')
def delete_file(request, id):
    file = fileentry.objects.get(id=id)
    file.delete()
    return JsonResponse({"success": "File wurde erfolgreich gelöscht"})

@login_required(login_url='login')
def update_file(request, id):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        place = request.POST.get('place', '')
        file = fileentry.objects.get(id=id)
        if title:
            file.title = title
        if place:
            if fileentry.objects.filter(place=place).exists():
                extra = fileentry.objects.get(place=place)
                extra.place = "nothing"
                extra.save()
            file.place = place 
        file.save()
        return JsonResponse({"success": "File wurde erfolgreich bearbeitet"})
    return JsonResponse({"error": "Etwas ist schief gelaufen. Versuche es später nochmal"})

# Delete File
@login_required(login_url='login')
def delete_file_by_name(request, name):
    try:
        cName = "yoolink/" + name
        docs = fileentry.objects.filter(file=cName)
        for doc in docs:
            doc.delete()
        """if docs.count() == 1:
            docs.first().delete()
        else:
            for doc in docs:
                doc.delete_model_only()"""
        return HttpResponse('')
        # Do something with the document
    except fileentry.DoesNotExist:
        # Handle the case where the document does not exist
        return JsonResponse({"error": "Dieses Image existiert nicht"})

# Displays all your uploaded images
@login_required(login_url='login')
def images_view(request):
    files = fileentry.objects.all()
    return render(request, "pages/cms/images.html", {"files": files})


# Resize the image (Aufloesung wird geaendert)
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

# Pixelgroese wird auf maximale Breite gesetzt
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


# Compress the image (Maximale Groese auf Limit setzten)
def compress_image(image):
    img = Image.open(image)
    buffer = BytesIO()

    target_size = 500 * 1024 # 500 KB
    quality = 100
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
        faqs = json.loads(request.POST.get('faqs', '[]'))
        for i, faq in enumerate(faqs):
            realFaq = FAQ.objects.get(id=faq['id'])
            realFaq.order = i + 1
            realFaq.question = faq['question']
            realFaq.answer = faq['answer']
            realFaq.save()
        return JsonResponse({'success': True})

    return JsonResponse({'error': True})


# --------------- [Blog] ---------------
@login_required(login_url='login')
def blog_view(request):
    data = {
        "blogs":  Blog.objects.all()
    }
    return render(request, "pages/cms/blog/blog.html", data)

# Delete Blog
@login_required(login_url='login')
def delete_blog(request, id):
    if request.method == 'POST':
        instance = get_object_or_404(Blog, id=id)
        instance.delete()
        return JsonResponse({'success': True}, status=200)
    return JsonResponse({'success': False}, status=400)


@login_required(login_url='login')
def create_blog(request):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        title = request.POST.get('title')

        if Blog.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Blog mit diesem Titel existiert bereits!'}, status=400)

        body = request.POST.get('body')
        code = json.loads(request.POST.get('code'))
        active = request.POST.get('active', False)
        
        title_image = request.FILES.get('title_image', '')
    
        #return JsonResponse({'title': title, 'body': body, 'code': code})

        if title:
            # Create
            blog = Blog(title=title, body=body, code=code, author=request.user)
            if active == "true":
                blog.active = True
            else:
                blog.active = False
            blog.save()
            resized_image = resize_image(title_image)
            scaled_image = scale_image(resized_image)
            compressed_image = compress_image(scaled_image)
            blog.title_image = compressed_image
            blog.save()
            return JsonResponse({'success': 'Blog successfully created', 'blogId': blog.id}, status=201)

        else:
            return JsonResponse({'error': 'Der Titel darf nicht leer sein!'}, status=400)

        # Do something with the POST parameters (e.g., save them to the database)
        # ...

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=400)

@login_required(login_url='login')
def update_blog(request, id):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        blog = get_object_or_404(Blog, id=id)

        title = request.POST.get('title')
        if blog.title != title and Blog.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Blog mit diesem Titel existiert bereits!'}, status=400)
        body = request.POST.get('body')
        code = json.loads(request.POST.get('code'))
        active = request.POST.get('active', False)
        title_image = request.FILES.get('title_image', '')

        if title:
            # Create
            blog.title = title
            blog.body = body 
            blog.code = code 
            if active == "true":
                blog.active = True
            else:
                blog.active = False
            if title_image:
                resized_image = resize_image(title_image)
                scaled_image = scale_image(resized_image)
                compressed_image = compress_image(scaled_image)
                blog.title_image = compressed_image
            blog.save()
            return JsonResponse({'success': 'Blog successfully updated', 'blogId': blog.id}, status=201)

        else:
            return JsonResponse({'error': 'Error request. Title is empty.'}, status=400)

    else:
        return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=400)


@login_required(login_url='login')
def add_blog(request):
            
    data = {
        "galerien": Galerie.objects.all()
    }

    return render(request, "pages/cms/blog/add_blog.html", data)

@login_required(login_url='login')
def blog_details(request, id):
    
    blog = get_object_or_404(Blog, id=id)

    data = {"blog": blog,"galerien": Galerie.objects.all()}

    return render(request, "pages/cms/blog/blog_update.html", data)

@login_required(login_url='login')
def blog_code(request, id):
    
    blog = get_object_or_404(Blog, id=id)

    data = {"code": blog.code, "success": "true"}

    return JsonResponse(data)


# --------------- [GALERY] ---------------
# Render Galery Detail View
@login_required(login_url='login')
def galery_view(request, id):
    galery = get_object_or_404(Galerie, id=id)
    return render(request, "pages/cms/galery/galery.html", {"galery": galery})

@login_required(login_url='login')
def get_galery_images(request):
    id = request.GET.get("galeryId")
    galery = get_object_or_404(Galerie, id=id)
    if galery.images:
        images_list = []
        for image in galery.images.all():
            image_dict = {
                'upload_url': image.upload.url,
                'uploaddate': image.uploaddate,
            }
            images_list.append(image_dict)
        return JsonResponse({"images": images_list}, status=200)
    return JsonResponse({}, status=400)
    
@login_required(login_url='login')
def update_galery_image(request, id):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        file = GaleryImage.objects.get(id=id)
        if title:
            file.title = title
            file.save()
            return JsonResponse({"success": "Bild wurde erfolgreich gespeichert"})
        return JsonResponse({"error": "Bitte gebe einen Titel ein!"})
    return JsonResponse({"error": "Etwas ist schief gelaufen. Versuche es später nochmal"})


# Render Galery Overview
@login_required(login_url='login')
def galerien(request):
    return render(request, "pages/cms/galery/galerien.html", {"galerien": Galerie.objects.all()})

# Create a galery
@login_required(login_url='login')
def create_galery(request):
    galery = Galerie.objects.create()
    # Generieren Sie die URL zur Detailseite des erstellten Modells
    url = reverse('cms:galery-view', args=[galery.id])
    # Leiten Sie auf die Detailseite des neuen Modells weiter
    return HttpResponseRedirect(url)

# Update a galery
@login_required(login_url='login')
def save_galery(request, id):
    galery = get_object_or_404(Galerie, id=id)
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        
        galery.title = title
        galery.description = description
        place = request.POST.get('place', 'nothing')
        if Galerie.objects.filter(place=place).exists():
            extra = Galerie.objects.get(place=place)
            extra.place = "nothing"
            extra.save()
        galery.place = place
        galery.save()
        return JsonResponse({"success": "Die Galerie wurde erfolgreich gespeichert"})
    return JsonResponse({"error": "Fehler beim Speichern der Galerie"})

# Upload Image for Galery
@login_required(login_url='login')
def upload_galery_img(request, id):
    if request.method == 'POST':
        my_file = request.FILES.get('file')
        resized_image = resize_image(my_file)
        scaled_image = scale_image(resized_image)
        compressed_image = compress_image(scaled_image)
        doc = GaleryImage.objects.create(upload=compressed_image)
        galery = Galerie.objects.get(id=id)
        galery.images.add(doc)
        galery.save()
        return HttpResponse('')
    return JsonResponse({'error': 'Falsche Anfrage (Erlaubt: POST)'})

# Delete File
@login_required(login_url='login')
def delete_galery_img(request, id):
    file = get_object_or_404(GaleryImage, id=id)
    file.delete()
    return JsonResponse({"success": "File wurde erfolgreich gelöscht"})


# Delete Galery
@login_required(login_url='login')
def delete_galery(request, id):
    if request.method == 'POST':
        galery = get_object_or_404(Galerie, id=id)
        for img in galery.images.all():
            img.delete()
        galery.delete()
        return JsonResponse({'success': 'Galerie wurde erfolgreich gelöscht'})
    return JsonResponse({'error': 'Falsche Anfrage (Erlaubt: POST)'})


# --------------- [Image Helper] ---------------
# get all images
@login_required(login_url='login')
def all_images(request):
    if request.method == 'GET':
        images = fileentry.objects.all()
        # Liste zur Speicherung der Bild-URLs erstellen
        image_urls = [] 

        # URLs für jedes fileentry-Objekt erstellen
        for entry in images:
            # URL für das Bild erstellen
            image_url = entry.file.url
            data = {
                "url": image_url,
                "id": entry.id
            }
            # URL zur Liste hinzufügen
            image_urls.append(data)

        # JSON-Antwort mit den Bild-URLs senden
        return JsonResponse({'image_urls': image_urls})
    return JsonResponse({'error': 'Falsche Anfrage (Erlaubt: GET)'})

# --------------- [Galery Helper] ---------------
# get all galerys
@login_required(login_url='login')
def all_galerien(request):
    if request.method == 'GET':
        galerien = Galerie.objects.all()
        galerien_list = []
        
        for galerie in galerien:
            images = galerie.images.all()  # Retrieve all related images for the galerie
            
            # Serialize each image object separately
            serialized_images = serializers.serialize('json', images)
            deserialized_images = serializers.deserialize('json', serialized_images)
            image_list = []
            
            # Loop through deserialized image objects to extract required fields
            for obj in deserialized_images:
                image = obj.object
                image_list.append({
                    'url': image.upload.url,
                    # Add other image fields as needed
                })
            
            galerien_list.append({
                'id': galerie.pk,
                'title': galerie.title,
                'description': galerie.description,
                'active': galerie.active,
                'images': image_list
                # Add other galerie fields as needed
            })
        
        return JsonResponse({'galerien': galerien_list}, safe=False)
    
    return JsonResponse({'error': 'Falsche Anfrage (Erlaubt: GET)'})


# Seiten
@login_required(login_url='login')
def content_view(request):
    return render(request, "pages/cms/content/content.html", {})

# Seiten
@login_required(login_url='login')
def site_view_main(request):
    return render(request, "pages/cms/content/sites/MainSite.html", {})

# Main Site - Hero Section
@login_required(login_url='login')
def site_view_main_hero(request):
    data = {}
    if TextContent.objects.filter(name="main_hero").exists():
        data["textContent"] = TextContent.objects.get(name='main_hero')
    if Galerie.objects.filter(place='main_hero').exists():
        data["heroImages"] = Galerie.objects.get(place='main_hero').images.all()
        
    return render(request, "pages/cms/content/sites/mainsite/HeroContent.html", data)

@login_required(login_url='login')
def site_view_main_responsive(request):
    data = {}
    if TextContent.objects.filter(name="main_responsive").exists():
        data["textContent"] = TextContent.objects.get(name='main_responsive')
    return render(request, "pages/cms/content/sites/mainsite/ResponsiveContent.html", data)

@login_required(login_url='login')
def site_view_main_cms(request):
    data = {}
    if TextContent.objects.filter(name="main_cms").exists():
        data["textContent"] = TextContent.objects.get(name='main_cms')
    if fileentry.objects.filter(place='main_cms').exists():
        data["cmsImage"] = fileentry.objects.get(place='main_cms')
    return render(request, "pages/cms/content/sites/mainsite/CmsContent.html", data)

@login_required(login_url='login')
def site_view_main_price(request):
    data = {}
    if TextContent.objects.filter(name="main_price").exists():
        data["textContent"] = TextContent.objects.get(name='main_price')
    return render(request, "pages/cms/content/sites/mainsite/PriceContent.html", data)

@login_required(login_url='login')
def site_view_main_team(request):
    data = {}
    if TextContent.objects.filter(name="main_team").exists():
        data["textContent"] = TextContent.objects.get(name='main_team')

    return render(request, "pages/cms/content/sites/mainsite/TeamContent.html", data)


@login_required(login_url='login')
def saveTextContent(request):
    if request.method == 'POST':
        header = request.POST.get('header', '')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        buttonText = request.POST.get('buttonText', '')
        # Model-Name: z.B. main_hero
        name = request.POST.get('name', '')

        customText = json.loads(request.POST.get('customText', '[]'))
        images = json.loads(request.POST.get('images', '[]'))
        galerien = json.loads(request.POST.get('galerien', '[]'))

        # Checks Images and updates their key
        for image in images:
            if fileentry.objects.filter(id=image["id"]).exists():
                file = fileentry.objects.get(id=image["id"])
                key = image['key']
                if key:
                    if fileentry.objects.filter(place=key).exists():
                        extra = fileentry.objects.get(place=key)
                        extra.place = "nothing"
                        extra.save()
                    file.place = key
                    file.save()

        for galery in galerien:
            if Galerie.objects.filter(id=galery['id']).exists():
                galerie = Galerie.objects.get(id=galery['id'])
                key = galery['key']
                if key:
                    if Galerie.objects.filter(place=key).exists():
                        extra = Galerie.objects.get(place=key)
                        extra.place = "nothing"
                        extra.save()
                    galerie.place = key
                    galerie.save()

        customKeys = []

        # Custom Text Update
        for custom in customText:
            key = custom['key']
            customKeys.append(key)
            if TextContent.objects.filter(name=key).exists():
                inputs = custom['inputs']
                textContent = TextContent.objects.get(name=key)
                # Set Values
                textContent.header = inputs.get('header', textContent.header)
                textContent.title = inputs.get('title', textContent.title)
                textContent.description = inputs.get('description', textContent.description)
                textContent.buttonText = inputs.get('buttonText', textContent.buttonText)
                textContent.save()
            else:
                inputs = custom['inputs']
                textContent = TextContent.objects.create(name=key, header=inputs.get('header', ''), title=inputs.get('title', ''), description=inputs.get('description', ''), buttonText=inputs.get('buttonText', ''))
                textContent.save()

        # Normal Text update
        if not name in customKeys:
            if TextContent.objects.filter(name=name).exists():
                # Create Model
                textContent = TextContent.objects.get(name=name)
                textContent.header = header
                textContent.title = title
                textContent.description = description
                textContent.buttonText = buttonText
                textContent.save()
                return JsonResponse({'success': 'Element wurde erfolgreich gespeichert'}, status=200)
            else:
                textContent = TextContent.objects.create(name=name, header=header, title=title, description=description, buttonText=buttonText)
                textContent.save()
                return JsonResponse({'success': 'Element wurde erfolgreich erstellt'}, status=201)
        return JsonResponse({'success': 'Elemente wurden erfolgreich gespeichert'}, status=200)

    return JsonResponse({'error': 'Etwas ist falsch gelaufen. Versuche es später nochmal'}, status=400)
