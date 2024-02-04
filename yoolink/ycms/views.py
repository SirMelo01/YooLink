import json
from django.shortcuts import get_object_or_404, render, redirect
from yoolink.ycms.models import fileentry, Review, FAQ, UserSettings, Order, Message, OrderItem, Galerie, Category, Brand, Blog, GaleryImage, TextContent, Product
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, F, DecimalField
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from .forms import fileform, Blogform
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from django.core.mail import send_mail
from .serializers import OrderSerializer
from yoolink.users.models import User
from .utils import send_payment_confirmation, send_ready_for_pickup_confirmation

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
        "product_count": Product.objects.count(),
        "order_count": Order.objects.filter(verified=True).count(),
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
        if place and not place == 'nothing':
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
        "blogs":  Blog.objects.all().order_by('-date')
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
        description = request.POST.get('description', '')
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
            blog.description = description
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
        description = request.POST.get('description', '')
        body = request.POST.get('body')
        code = json.loads(request.POST.get('code'))
        active = request.POST.get('active', False)
        title_image = request.FILES.get('title_image', '')

        if title:
            # Create
            blog.description = description
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
        if not place == 'nothing':
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

    if Galerie.objects.filter(place='main_responsive_desktop').exists():
        data['responsiveDesktopImages'] = Galerie.objects.get(place='main_responsive_desktop').images.all()
        
    if Galerie.objects.filter(place='main_responsive_handy').exists():
        data['responsiveHandyImages'] = Galerie.objects.get(place='main_responsive_handy').images.all()

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


"""
Products
"""
@login_required(login_url='login')
def product_view(request):
    return render(request, "pages/cms/products/overview.html", {"products": Product.objects.all()})

@login_required(login_url='login')
def product_create_view(request):
    return render(request, "pages/cms/products/create-product.html", {})

@login_required(login_url='login')
def product_detail(request, product_id, slug):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "pages/cms/products/edit-product.html", {"product": product})

@login_required(login_url="login")
def product_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(title__icontains=query)
    else:
        products = Product.objects.all()

    data = []
    for product in products:
        data.append({
            'title': product.title,
            'description': product.description,
            'price': product.price,
            'discount_price': product.discount_price if product.is_reduced else None,
            'image_url': 'https://www.kovinc.de/wp-content/uploads/2021/02/schweissen-fuer-einsteiger.jpg',
            # Add other fields as needed
        })

    return JsonResponse({'products': data})

@login_required(login_url='login')
def product_create(request):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        title = request.POST.get('title')

        if Product.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Produkt mit diesem Titel existiert bereits!'}, status=400)

        description = request.POST.get('description', '')
        # Create hersteller and selected_categories
        hersteller = request.POST.get('hersteller', '')
        selected_categories_json = request.POST.get('selected_categories')
        selected_categories = json.loads(selected_categories_json) if selected_categories_json else []
        
        active = request.POST.get('isActive', False)
        inStock = request.POST.get('isInStock', False)
        isReduced = request.POST.get('isReduced', False)
        price_str = request.POST.get('price', '0')
        reduced_price_str = request.POST.get('reducedPrice', price_str)
        # Remove commas and convert to float
        price = float(price_str.replace(',', '.'))
        reduced_price = price
        if reduced_price_str:
            reduced_price = float(reduced_price_str.replace(',', '.'))

        title_image = request.FILES.get('title_image', '')
        gallery = request.POST.get('galeryId', '')
        
        # Now you can use 'price' and 'reduced_price' as numeric values in your if condition
        if title and price > 0:
            # Create
            product = Product(
                title=title, 
                description=description, 
                price=price,
                discount_price=reduced_price)
            if active == "true":
                product.is_active = True
            else:
                product.is_active = False
            if inStock == "true":
                product.is_in_stock = True
            else:
                product.is_in_stock = False
            if isReduced == "true":
                product.is_reduced = True
            else:
                product.is_reduced = False
            # Brand
            if hersteller:
                brand, created = Brand.objects.get_or_create(name=hersteller, defaults={'website': ''})
                product.brand = brand
            # Categories
            with transaction.atomic():
                # Create or get Brand by hersteller and associate it with the product

                for category_name in selected_categories:
                    category, created = Category.objects.get_or_create(name=category_name)
                    product.categories.add(category)

                # Save the product
                product.save()
            # Gallery
            if gallery:
                galleryModel = get_object_or_404(Galerie, id=int(gallery))
                if galleryModel:
                    product.gallery = galleryModel
                else:
                    return JsonResponse({'error': 'Die angegebene Galerie konnte nicht gefunden werden'}, status=400)
 
            product.save()
            resized_image = resize_image(title_image)
            scaled_image = scale_image(resized_image)
            compressed_image = compress_image(scaled_image)
            product.title_image = compressed_image
            product.save()
            return JsonResponse({'success': 'Product successfully created', 'productId': product.id, 'slug': product.slug}, status=201)

        else:
            return JsonResponse({'error': 'Der Titel darf nicht leer sein und der Preis muss größer 0 sein!'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=400)

@login_required(login_url='login')
def product_update(request, product_id, slug):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        title = request.POST.get('title')

        if not Product.objects.filter(id=product_id).exists():
            return JsonResponse({'error': 'Dieses Produkt existiert nicht.'}, status=400)
        product = Product.objects.get(id=product_id)    
        if title != product.title and Product.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Produkt mit diesem Titel existiert bereits!'}, status=400)

        description = request.POST.get('description', '')
        # Create hersteller and selected_categories
        hersteller = request.POST.get('hersteller', '')
        selected_categories_json = request.POST.get('selected_categories')
        selected_categories = json.loads(selected_categories_json) if selected_categories_json else []

        active = request.POST.get('isActive', False)
        inStock = request.POST.get('isInStock', False)
        isReduced = request.POST.get('isReduced', False)
        price_str = request.POST.get('price', '0')
        reduced_price_str = request.POST.get('reducedPrice', price_str)
        # Remove commas and convert to float
        price = float(price_str.replace(',', '.'))
        reduced_price = price
        if reduced_price_str:
            reduced_price = float(reduced_price_str.replace(',', '.'))

        title_image = request.FILES.get('title_image', '')
        gallery = request.POST.get('galeryId', '')

        # Now you can use 'price' and 'reduced_price' as numeric values in your if condition
        if title and price > 0:
            # Create
            # Create or get Brand by hersteller and associate it with the product
            if hersteller:
                brand, created = Brand.objects.get_or_create(name=hersteller, defaults={'website': ''})
                product.brand = brand

            # Handle categories
            with transaction.atomic():
                # Create or get Brand by hersteller and associate it with the product

                # Handle categories
                product.categories.clear()  # Clear existing categories

                for category_name in selected_categories:
                    category, created = Category.objects.get_or_create(name=category_name)
                    product.categories.add(category)

                # Save the product
                product.save()

            if gallery:
                galleryModel = get_object_or_404(Galerie, id=int(gallery))
                if galleryModel:
                    product.gallery = galleryModel
                else:
                    return JsonResponse({'error': 'Die angegebene Galerie konnte nicht gefunden werden'}, status=400)

            product.title = title
            product.description = description
            product.price = price 
            product.discount_price = reduced_price

            if active == "true":
                product.is_active = True
            else:
                product.is_active = False
            if inStock == "true":
                product.is_in_stock = True
            else:
                product.is_in_stock = False
            if isReduced == "true":
                product.is_reduced = True
            else:
                product.is_reduced = False
            product.save()
            if title_image:
                resized_image = resize_image(title_image)
                scaled_image = scale_image(resized_image)
                compressed_image = compress_image(scaled_image)
                product.title_image = compressed_image
                product.save()
            return JsonResponse({'success': 'Product successfully updated', 'productId': product.id, 'slug': product.slug}, status=201)

        else:
            return JsonResponse({'error': 'Der Titel darf nicht leer sein und der Preis muss größer 0 sein!'}, status=400)

    else:
        return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=400)

@login_required(login_url='login')
def get_categories(request):
    categories = list(Category.objects.values_list('name', flat=True))
    return JsonResponse({'categories': categories})

@login_required(login_url='login')
def get_brands(request):
    brands = list(Brand.objects.values_list('name', flat=True))
    return JsonResponse({'brands': brands})

@login_required(login_url='login')
def product_delete(request, product_id, slug):
    if request.method == 'POST':
        instance = get_object_or_404(Product, id=product_id)
        instance.delete()
        return JsonResponse({'success': True}, status=200)
    return JsonResponse({'success': False}, status=400)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def search_products(request):
    name_query = request.GET.get('name')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    manufacturer = request.GET.get('manufacturer')
    category = request.GET.get('category')
    is_active = True  # Must be True
    is_in_stock = request.GET.get('is_in_stock', True)
    is_reduced = request.GET.get('is_reduced')

    products = Product.objects.filter(is_active=is_active, is_in_stock=is_in_stock)

    if is_reduced:
        #products = products.filter(is_reduced__icontains=name_query)
        pass

    if name_query:
        products = products.filter(title__icontains=name_query)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if manufacturer:
        products = products.filter(brand__name__icontains=manufacturer)

    if category:
        products = products.filter(categories__name__icontains=category)

    data = list(products.values())
    return JsonResponse(data, safe=False)


"""
Orders
"""

@login_required(login_url='login')
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "pages/cms/orders/detail.html", {'order': order})

@login_required(login_url='login')
def order_view(request):
    # Count of all orders
    total_orders = Order.objects.filter(verified=True).count()

    # Umsatz (total revenue)
    desired_statuses = ['COMPLETED', 'PAID']

    # Calculate total revenue for orders with the desired statuses
    total_revenue = Order.objects.filter(status__in=desired_statuses, verified=True).aggregate(
        total_revenue=Sum('items__unit_price')
    )['total_revenue'] or 0
    # Number of clients
    total_clients = Order.objects.filter(verified=True).values('buyer_email').distinct().count()

    # Open orders (not closed/paid)
    open_orders = Order.objects.filter(status='OPEN', verified=True).count()

    # Most bought products
    most_bought_products = OrderItem.objects.values(
    'product__title',
    'product__title_image',
).annotate(
    total_quantity=Sum('quantity'),
    total_cash=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
).order_by('-total_quantity')[:5]

    # Biggest buyers
    biggest_buyers = Order.objects.filter(verified=True).values('buyer_email').annotate(total_spent=Sum('items__unit_price')).order_by('-total_spent')[:5]

    all_orders = Order.objects.filter(verified=True).order_by('-created_at')

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_clients': total_clients,
        'open_orders': open_orders,
        'most_bought_products': most_bought_products,
        'biggest_buyers': biggest_buyers,
        'all_orders': all_orders,
    }

    return render(request, "pages/cms/orders/overview.html", context)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_order_status_admin(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get('status')
    order.status = new_status
    order.save()
    return Response({'success': 'Auftragsstatus wurde erfolgreich angepasst'}, status=status.HTTP_200_OK)

# views.py
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_review(request, review_id):
    try:
        review = Review.objects.get(pk=review_id)
        review.delete()
        return Response({'success': 'Review wurde erfolgreich gelöscht'}, status=status.HTTP_200_OK)
    except Review.DoesNotExist:
        return Response({'error': 'Bewertung nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)

# views.py
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        order.delete()
        return Response({'success': 'Auftrag wurde erfolgreich gelöscht'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Auftrag nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)

# views.py

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_order_by_id(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    order_serializer = OrderSerializer(order)
    
    return Response(order_serializer.data, status=status.HTTP_200_OK)

# views.py
from django.db.models import Q
from datetime import timezone, timedelta

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_orders(request):
    status_filter = request.GET.get('status')
    buyer_email_filter = request.GET.get('buyer_email')
    last_period_filter = request.GET.get('last_period')

    orders = Order.objects.all()

    if status_filter:
        orders = orders.filter(status=status_filter)

    if buyer_email_filter:
        orders = orders.filter(buyer_email=buyer_email_filter)

    if last_period_filter:
        if last_period_filter == '1_year':
            start_date = timezone.now() - timedelta(days=365)
        elif last_period_filter == '30_days':
            start_date = timezone.now() - timedelta(days=30)
        elif last_period_filter == '1_week':
            start_date = timezone.now() - timedelta(weeks=1)
        elif last_period_filter == '1_day':
            start_date = timezone.now() - timedelta(days=1)
        else:
            return Response({'error': 'Invalid last_period parameter'}, status=status.HTTP_400_BAD_REQUEST)

        orders = orders.filter(created_at__gte=start_date)

    data = list(orders.values()) if orders.exists() else []
    return JsonResponse(data, safe=False)

# USER Endpoints

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order_id = request.session.get('order_id')
    cart_amount = request.session.get('cart_amount')
    if not cart_amount:
        cart_amount = 0
    order = None
    if not order_id:
        order = Order.objects.create(buyer_email='')
        request.session['order_id'] = order.id
    else:
        order = Order.objects.get(id=order_id)

    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        product=product,
        is_discounted=product.is_reduced,
        unit_price=product.discount_price if product.is_reduced else product.price
    )
    if not created:
        order_item.quantity += 1
        order_item.save()
    else:
        request.session['cart_amount'] = int(cart_amount) + 1
    return JsonResponse({'success': 'Produkt wurde erfolgreich zum Warenkorb hinzugefügt'})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def cart_items(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return JsonResponse({"error": "There is no Cart yet. Add Items to it first."})
    order = Order.objects.get(id=order_id) if order_id else None
    total_price = 0.0
    if order:
        cart_items = [{
            'product_title': item.product.title,
            'quantity': item.quantity,
            'price': float(item.get_price()),
            'subtotal': float(item.subtotal())
        } for item in order.items.all()]
        total_price = float(order.total())
    else:
        cart_items = []

    return JsonResponse({'cart_items': cart_items, 'total_price': total_price})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def remove_from_cart(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    order_id = request.session.get('order_id', None)

    if order_id and order_item in Order.objects.get(id=order_id).items.all():
        Order.objects.get(id=order_id).items.remove(order_item)
        return JsonResponse({'success': 'Produkt wurde erfolgreich vom Warenkorb entfernt'})
    
    return JsonResponse({'error': 'Etwas ist schiefgelaufen. Versuche es später erneut'})
        
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def update_quantity(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    new_quantity = int(request.POST.get('quantity', 1))
    order_id = request.session.get('order_id')
    order = Order.objects.get(id=order_id) if order_id else None

    if not order:
        return JsonResponse({'error': 'Order not found in session'})
    # Überprüfe, ob das Produkt reduziert ist und ob die Menge nicht mehr geändert werden kann
    if order_item.product.is_reduced and not order_item.is_discounted:
        return JsonResponse({'error': 'Quantity cannot be updated for this product'})

    order_item.quantity = new_quantity
    order_item.save()

    return JsonResponse({'success': 'Quantity updated successfully'})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def update_cart_items(request):
    order_id = request.session.get('order_id')
    order = Order.objects.get(id=order_id) if order_id else None

    if not order:
        return JsonResponse({'error': 'Order not found in session'})

    cart_items_data = request.data.get('cart_items', [])
    
    for item_data in cart_items_data:
        order_item_id = item_data.get('order_item_id')
        new_quantity = item_data.get('quantity')

        order_item = get_object_or_404(OrderItem, id=order_item_id, order=order)

        # Only update quantity if it's different from the original one
        if order_item and new_quantity is not None and new_quantity != order_item.quantity:
            order_item.quantity = new_quantity
            order_item.save()

    # Update total price in the session
    request.session['cart_total_price'] = float(order.total())

    return JsonResponse({'success': 'Cart items updated successfully'})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def verify_cart(request):
    buyer_email = request.POST.get('buyer_email')
    buyer_name = request.POST.get('buyer_name')

    if not buyer_email or not buyer_name:
        return JsonResponse({'error': 'Buyer email and buyer name are required parameters'}, status=400)

    order_id = request.session.get('order_id')
    order = Order.objects.get(id=order_id) if order_id else None

    if not order or order.status != 'OPEN' or order.verified:
        request.session['order_id'] = None  # Clear session order
        return JsonResponse({'error': 'Invalid order for verification'}, status=400)

    # Check linked prices for OrderItems
    for item in order.items.all():
        if (item.product.is_reduced and not item.is_discounted) or (not item.product.is_reduced and item.is_discounted):
            return JsonResponse({'error': f'Invalid price configuration for {item.product.title}'}, status=400)

    # Update Order Data
    order.buyer_email = buyer_email
    # order.buyer_name = buyer_name
    order.save()

    # Generate verification link
    token = str(order.uuid)
    verification_url = request.scheme + '://' + request.get_host() + reverse('cms:verify_order') + f'?token={token}&order_id={order_id}'
    # Send confirmation email with verification link
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()
    full_name = user_settings.full_name
    company_name = user_settings.company_name
    phone_number = user_settings.tel_number
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website

    subject = f"Ihr Auftrag {order.id}"
    message = f"Hallo {buyer_name},\n\nVielen Dank für Ihren Auftrag bei {company_name}. Ihr Auftrag mit der Auftragsnummer {order.id} wurde erfolgreich bestätigt. Hier sind die Details Ihres Auftrags:\n\n"

    for item in order.items.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"

    message += f"\nGesamtpreis: {order.total():.2f} Euro\n\n"
    message += f"Wir haben Ihren Auftrag erhalten und benötigen noch eine Bestätigung von Ihnen, um fortzufahren. Bitte klicken Sie auf den folgenden Link, um Ihren Auftrag zu bestätigen und zur Kasse zu gelangen:\n{verification_url}\n\n"
    message += f"Nach erfolgreicher Bestätigung können Sie Ihre Ware bestellen oder abholen.\n\nVielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{full_name}"
    message += f"\n{company_name}"

    if phone_number and phone_number != "0":
        message += f"\nTel. {phone_number}"

    if fax_number and fax_number != "0":
        message += f"\nFax {fax_number}"

    if mobile_number and mobile_number != "0":
        message += f"\nHandy {mobile_number}"

    if website:
        message += f"\n{website}"
    message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )

    return JsonResponse({'success': 'Order verification email sent successfully'})

@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([])
def update_shipping_address(request, order_id):
    new_shipping_address = request.POST.get('shipping_address')

    if not new_shipping_address:
        return JsonResponse({'error': 'New shipping address is required'}, status=400)

    order = get_object_or_404(Order, id=order_id)

    if not order.verified:
        return JsonResponse({'error': 'Product is not verified yet. Please check your emails'}, status=400)

    # Update shipping address
    order.buyer_address = new_shipping_address
    order.save()

    return JsonResponse({'success': 'Shipping address updated successfully'})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not order:
        return JsonResponse({'error': 'The order does not exist'}, status=400)
    old_status = order.status
    if old_status != 'OPEN':
        return JsonResponse({'error': 'The order was already checked-out'}, status=400)
    
    order.status = 'PAID'
    order.save()
    send_payment_confirmation(order)
    return JsonResponse({'success': f'The payment for the order #{order.id} was successful. You should get a confirmation email to the following email soon: {order.buyer_email}'})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def api_order_error(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not order:
        return JsonResponse({'error': 'The order does not exist'}, status=400)
    old_status = order.status
    if old_status != 'OPEN':
        return JsonResponse({'error': 'The order was already checked-out'}, status=400)
    
    return JsonResponse({'error': 'This is the order payment error route. Something went wrong while trying to pay for the order'})

from paypal.standard.forms import PayPalPaymentsForm
def checkout_view(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return JsonResponse({"error": "There is no Cart yet. Add Items to it first."}, status=400)
    order = Order.objects.get(id=order_id) if order_id else None
    if not order.verified:
        return JsonResponse({"error": "The order is not yet verified"}, status=400)
    if order.status != 'OPEN':
        return JsonResponse({"error": "The order is not open anymore"}, status=400)

    total_price = 0.0
    if order:
        cart_items = [{
            'product_title': item.product.title,
            'quantity': item.quantity,
            'price': float(item.get_price()),
            'subtotal': float(item.subtotal())
        } for item in order.items.all()]
        total_price = float(order.total())
    else:
        cart_items = []

    # What you want the button to do.
    host = request.get_host()

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": order.total,
        "item_name": "Auftrag #" + str(order.id),
        "invoice": str(order.uuid),
        "currency_code": 'EUR',
        "notify_url": 'https://{}{}'.format(host, reverse('paypal_ipn')),
        "return": 'https://{}{}'.format(host, reverse('cms:api-order-payment-success', kwargs={'order_id': order.id})),
        "cancel_return": 'https://{}{}'.format(host, reverse('cms:api-order-payment-error', kwargs={'order_id': order.id})),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)

    context = {
        'cart_items': cart_items, 
        'total_price': total_price,
        'order': order,
        'form': form
    }
    return render(request, "pages/cms/orders/checkout.html", context)

# Check Out View with id
def checkout_view_id(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not order.verified:
        return JsonResponse({"error": "The order is not yet verified"}, status=400)
    if order.status != 'OPEN':
        return JsonResponse({"error": "The order is not open anymore"}, status=400)

    total_price = 0.0
    if order:
        cart_items = [{
            'product_title': item.product.title,
            'quantity': item.quantity,
            'price': float(item.get_price()),
            'subtotal': float(item.subtotal())
        } for item in order.items.all()]
        total_price = float(order.total())
    else:
        cart_items = []

    # What you want the button to do.
    host = request.get_host()

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": order.total,
        "item_name": "Auftrag #" + str(order.id),
        "invoice": str(order.uuid),
        "currency_code": 'EUR',
        "notify_url": 'https://{}{}'.format(host, reverse('paypal_ipn')),
        "return": 'https://{}{}'.format(host, reverse('cms:api-order-payment-success', kwargs={'order_id': order.id})),
        "cancel_return": 'https://{}{}'.format(host, reverse('cms:api-order-payment-error', kwargs={'order_id': order.id})),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)

    context = {
        'cart_items': cart_items, 
        'total_price': total_price,
        'order': order,
        'form': form
    }
    return render(request, "pages/cms/orders/checkout.html", context)


@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([])
def update_order_status_by_user(request, order_id):
    new_status = request.PATCH.get('new_status')

    if not new_status:
        return JsonResponse({'error': 'New status is required'}, status=400)

    order = get_object_or_404(Order, id=order_id)
    old_status = order.status

    # Check if the new status is allowed based on the old status
     # Check if the new status is allowed based on the old status
    allowed_status_transitions = {
        'OPEN': ['PAID', 'READY_FOR_PICKUP'],
    }

    if new_status not in allowed_status_transitions.get(old_status, []):
        return JsonResponse({'error': f'Invalid status transition from {old_status} to {new_status}'}, status=400)

   
    # Update order status
    order.status = new_status
    order.save()

    # Send confirmation emails based on status change
    if old_status == 'OPEN' and new_status in ['PAID', 'READY_FOR_PICKUP']:
        if new_status == 'PAID':
            send_payment_confirmation(order)
        elif new_status == 'READY_FOR_PICKUP':
            send_ready_for_pickup_confirmation(order)
        else:
             return JsonResponse({'error': f'The new status {new_status} cannot be used here'})
    else:
        return JsonResponse({'error': 'Something went wrong!'})

    return JsonResponse({'success': 'Order status updated successfully'})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_order(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity')
    buyer_email = request.data.get('email')
    buyer_name = request.data.get('name')
    if not buyer_email or not buyer_name:
        return Response({'error': 'Es wurde keine Email oder Name angegeben'}, status=status.HTTP_401_UNAUTHORIZED)
    if not quantity or not product_id:
        return Response({'error': 'Es wurde kein Produkt angegeben'}, status=status.HTTP_401_UNAUTHORIZED)
    # Check if the product exists
    product = get_object_or_404(Product, id=product_id)
    # Corrected code to get user settings for staff user
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()

    # Check if a staff user with settings exists
    if user_settings is None:
        return Response({'error': 'No staff user with settings found'}, status=status.HTTP_404_NOT_FOUND)
    # Check if the product is discounted
    is_discounted = product.is_reduced
    unit_price = product.discount_price if is_discounted else product.price

    # Create order item
    order_item = OrderItem.objects.create(
        product=product,
        quantity=quantity,
        is_discounted=is_discounted,
        unit_price=unit_price
    )

    # Create order
    order = Order.objects.create(buyer_email=buyer_email)
    order.items.add(order_item)
    order.save()

    # User Data
    full_name = user_settings.full_name
    company_name = user_settings.company_name
    phone_number = user_settings.tel_number
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website

    # Send confirmation emails (use your preferred method)
    subject = f"Ihr Auftrag {order.id}"
    message = f"Hallo {buyer_name},\n\nVielen Dank für Ihren Auftrag bei {company_name}. Wir freuen uns, Ihnen mitzuteilen, dass Ihr Auftrag mit der Auftragsnummer {order.id} erfolgreich eingegangen ist. Unten finden Sie die Details Ihrem Auftrag:\n\n"

    # Add details of each ordered item
    for item in order.items.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"


    message += f"\nGesamtpreis: {order.total():.2f} Euro\n\n"
    #message += "Wir werden Ihren Auftrag so schnell wie möglich bearbeiten und Ihnen alle weiteren Informationen mitteilen.\n\n"
    dashboard_url = settings.DASHBOARD_URL
    url = dashboard_url + "cms/order/verify/?token=" + str(order.uuid) + "&order_id=" + str(order.id)
    message += f"\nBitte bestätigen sie ihren Auftrag hier: {url}"
    message += f"\nVielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{full_name}"
    message += f"\n{company_name}"

    if phone_number and phone_number != "0":
        message += f"\nTel. {phone_number}"

    if fax_number and fax_number != "0":
        message += f"\nFax {fax_number}"

    if mobile_number and mobile_number != "0":
        message += f"\nHandy {mobile_number}"

    if website:
        message += f"\n{website}"
    message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )


    return Response({'success': True}, status=status.HTTP_201_CREATED)


def order_verify_view(request):
    token = request.GET.get('token')
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, uuid=token)
    return render(request, "pages/cms/orders/verify.html", {"order": order})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def verify_order(request):
    orderId = request.POST.get('orderId')
    uuid = request.POST.get('uuid')
    address = request.POST.get('address')
    payment = request.POST.get('payment')
    if not orderId or not uuid:
        return JsonResponse({'error': 'orderId and uuid are required.'}, status=400)
    
    if not address:
        return JsonResponse({'error': 'Die Adresse muss angegeben sein'}, status=400)

    # Check if the order exists
    order = get_object_or_404(Order, id=orderId, uuid=uuid)
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()
    if not user_settings:
        return JsonResponse({'error': 'There is no staff user!.'}, status=400)
    # Check if the order is not already verified
    if not order.verified:
        # Set the order as verified
        order.verified = True
        order.save()
        # User Data
        full_name = user_settings.full_name
        company_name = user_settings.company_name
        phone_number = user_settings.tel_number
        email = user_settings.email
        fax_number = user_settings.fax_number
        mobile_number = user_settings.mobile_number
        website = user_settings.website
        # Send confirmation emails (use your preferred method)
        subject = f"Bestätigung Auftrag {order.id}"
        message = f"Vielen Dank für die Bestätigung Ihres Auftrags bei {company_name}."
        message += "\nWir werden Ihren Auftrag so schnell wie möglich bearbeiten und Ihnen alle weiteren Informationen mitteilen.\n\n"
        message += f"Vielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{full_name}"
        message += f"\n{company_name}\nTel. {phone_number}\nFax {fax_number}\nHandy {mobile_number}\n{website}"
        message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.buyer_email],
            fail_silently=False,
        )

        # Email an Unternehmen
        dashboard_url = settings.DASHBOARD_URL

        subject_company = "Neue Bestellung eingegangen"
        message_company = f"Hallo Team,\n\nEine neue Bestellung ist eingegangen. Bitte schauen Sie im Dashboard nach, um weitere Details zu erhalten.\n\n"
        message_company += f"Sie können die Bestellung hier einsehen: {dashboard_url}cms/orders/{order.id}/\n\n"
        message_company += "Vielen Dank!\n\nMit freundlichen Grüßen,\nIhr YooLink"

        
        # Replace 'your_company_email' with the actual email address of your company
        send_mail(
            subject_company,
            message_company,
            settings.EMAIL_HOST_USER,
            [email],  # Add additional recipients if needed
            fail_silently=False,
        )

        return JsonResponse({'success': 'Order successfully verified.'})
    else:
        return JsonResponse({'error': 'Order is already verified.'}, status=400)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def email_send(request):
    message = request.data.get('message')
    email = request.data.get('email')
    title = request.data.get('title')
    name = request.data.get('name', 'Unbekannt')
    
    if not message or not email or not title or not name:
        return Response({'error': 'Es fehlen Parameter bei der Anfrage'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Hier könntest du den Namen des Anfragenden hinzufügen, wenn dieser verfügbar ist
    # z.B., angenommen, dass der Name in den Anfrage-Daten als 'name' vorhanden ist
    
    
    # Email an Unternehmen
    dashboard_url = settings.DASHBOARD_URL
    existing_message = Message.objects.filter(name=name, message=message, email=email, title=title).first()

    if existing_message:
        # Return an error response indicating that a similar message already exists
        response_data = {'error': 'Sie haben diese Nachricht bereits gesendet'}
        return JsonResponse(response_data, status=400)
    message = Message.objects.create(name=name,message=message,email=email,title=title)

    subject_company = "Neue Nachricht in Ihrem CMS"
    message_company = f"Hallo Team,\n\n{ name } ({ email }) hat eine neue Anfrage gesendet:\n\n"
    message_company += f"Betreff: { title }\n\n"
    message_company += f"Nachricht: { message }\n\n"
    message_company += f"Bitte schauen Sie im Dashboard nach, um weitere Details zu erhalten: {dashboard_url}cms/messages/{message.id}\n\n"
    message_company += "Vielen Dank!\n\nMit freundlichen Grüßen,\nIhr YooLink"
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()
    # Replace 'your_company_email' with the actual email address of your company
    send_mail(
        subject_company,
        message_company,
        settings.EMAIL_HOST_USER,
        [user_settings.email],  # Add additional recipients if needed
        fail_silently=False,
    )

    return Response({'success': True}, status=status.HTTP_200_OK)

# Settings
@login_required(login_url='login')
def user_settings_view(request):
    # Retrieve the UserSettings for the currently logged-in user or any specific user
    user_settings = UserSettings.objects.get(user=request.user)

    context = {
        'settings': user_settings,
        # Other context variables if needed
    }

    return render(request, 'pages/cms/settings/settings.html', context)

@login_required(login_url='login')
def user_settings_update(request):
    if request.method == 'POST':
        user_settings = UserSettings.objects.get(user=request.user)

        # Update user settings based on the received data
        user_settings.email = request.POST.get('email', '')
        user_settings.full_name = request.POST.get('full_name', '')
        user_settings.company_name = request.POST.get('company_name', '')
        user_settings.tel_number = request.POST.get('tel_number', '')
        user_settings.fax_number = request.POST.get('fax_number', '')
        user_settings.mobile_number = request.POST.get('mobile_number', '')
        user_settings.website = request.POST.get('website', '')

        # Save the updated user settings
        user_settings.save()

        return JsonResponse({'success': 'Die Einstellungen wurden erfolgreich gespeichert'})
    else:
        return JsonResponse({'error': 'Die Einstellungen konnten nicht gespeichert werden'})