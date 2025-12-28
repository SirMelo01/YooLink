from datetime import datetime
import json
import os
import re
from yoolink.forms import ContactForm
from yoolink.views import get_opening_hours
from django.shortcuts import get_object_or_404, render, redirect
from yoolink.ycms.models import AnyFile, Button, Notification, PricingCard, PricingFeature, TeamMember, VideoFile, fileentry, OpeningHours, ShippingAddress, Review, FAQ, UserSettings, Order, Message, OrderItem, Galerie, Category, Brand, Blog, GaleryImage, TextContent, Product
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, F, DecimalField
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from .forms import fileform, Blogform
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from django.core.mail import send_mail
from .serializers import OrderSerializer, OrderItemSerializer
from yoolink.users.models import User
from rest_framework.permissions import IsAuthenticated
from django.middleware.csrf import get_token
from .utils import send_payment_confirmation, send_ready_for_pickup_confirmation, send_shipping_confirmation
from django.views.decorators.csrf import csrf_exempt
from django.templatetags.static import static
from django.utils import translation

DEFAULT_LANGUAGE = "en"

def get_active_language(request):
    """Holt die aktuelle Sprache aus dem Request oder setzt Fallback auf 'en'"""
    lang = get_language_from_request(request)  # Browser-Sprache holen
    available_languages = dict(settings.LANGUAGES)  # Unterstützte Sprachen aus settings.py

    if lang not in available_languages:
        lang = "en"  # Standard-Sprache setzen

    activate(lang)  # Sprache für diese Anfrage aktiv setzen
    return lang

@login_required
def cms_set_language(request, lang_code):
    """
    Sprache nur für das CMS setzen (ohne /en-Prefix).
    Nutzt Cookie (wie das eingebaute set_language).
    """
    available_languages = dict(settings.LANGUAGES)

    if lang_code not in available_languages:
        return JsonResponse({'error': 'Invalid language'}, status=400)

    # Sprache für diese Request aktivieren
    activate(lang_code)

    # Cookie setzen – LocaleMiddleware liest das beim nächsten Request
    response = JsonResponse({'message': 'Language changed', 'language': lang_code})
    response.set_cookie(
        getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language"),
        lang_code,
        max_age=60 * 60 * 24 * 30,  # 30 Tage
        path="/",
    )
    return response

def set_mt_fields(instance, lang, payload):
    """
    payload = dict mit evtl. Keys: title, description, alt_text, tags, place
    Setzt <field>_<lang>; für Default-Sprache zusätzlich das Basisfeld.
    """
    for field in ('title', 'description', 'alt_text', 'tags', 'place'):
        val = (payload.get(field) or '').strip()
        if val == '':
            continue
        setattr(instance, f'{field}_{lang}', val)
        if lang == DEFAULT_LANGUAGE:
            setattr(instance, field, val)

def ensure_video_slug(instance, source_title):
    """
    Erzeuge einen eindeutigen Slug, falls keiner gesetzt ist.
    Nutzt den übergebenen Titel (der in beliebiger Sprache sein kann),
    ohne das Basisfeld (title) zu überschreiben.
    """
    if instance.slug:
        return
    base_slug = slugify(source_title) or 'video'
    slug = base_slug
    i = 1
    while VideoFile.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    instance.slug = slug

def get_or_create_translated_blog(request, id):
    lang = get_active_language(request)
    blog = get_object_or_404(Blog, id=id)

    # Finde Original
    original_blog = blog.original if blog.original else blog

    # Wenn Original bereits die richtige Sprache hat → zurückgeben
    if original_blog.language == lang:
        return original_blog

    # Prüfen ob Variante existiert
    variant = original_blog.translations.filter(language=lang).first()
    if variant:
        return variant

    # Neue Variante anlegen
    new_blog = Blog.objects.create(
        title=original_blog.title,
        slug=original_blog.slug + '-' + lang,
        title_image=original_blog.title_image,
        author=original_blog.author,
        body=original_blog.body,
        code=original_blog.code,
        active=False,
        description=original_blog.description,
        language=lang,
        original=original_blog,
    )
    return new_blog

@login_required(login_url='login')
def cms_files(request):
    data = {
        "file_count":  fileentry.objects.count(),
        'anyfile_count': AnyFile.objects.count(),
        'videofile_count': VideoFile.objects.count(),
    }
    return render(request, 'pages/cms/files/files.html', data)

@login_required(login_url='login')
def cms(request):

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
        "file_count":  fileentry.objects.count(),
        "button_count": Button.objects.count(),
        "galery_count":  Galerie.objects.count(),
        "blog_count": Blog.objects.filter(original__isnull=True).count(),
        "product_count": Product.objects.count(),
        "order_count": Order.objects.filter(verified=True).count(),
        "order_not_closed_count": Order.objects.exclude(status='COMPLETED').count(),
        'form': form,
        'anyfile_count': AnyFile.objects.count(),
        'videofile_count': VideoFile.objects.count()
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
        lang = get_active_language(request)
        if title:
            setattr(file, f'title_{lang}', title)

            # Falls Standardsprache → auch Hauptfeld setzen
            if lang == DEFAULT_LANGUAGE:
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
    # wie viele pro Seite (Default 24)
    try:
        per_page = max(1, min(200, int(request.GET.get('per_page', 24))))
    except ValueError:
        per_page = 24

    qs = fileentry.objects.all().order_by('-uploaddate')

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    preserved = request.GET.copy()
    preserved.pop('page', None)  # Page raus für die Links
    querystring = preserved.urlencode()

    return render(
        request,
        "pages/cms/images.html",
        {
            "files": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "per_page": per_page,
            "querystring": querystring,
            "total_count": paginator.count,
        },
    )

def resize_image(image):
    """
    Resize the image without changing its resolution and format.
    """
    img = Image.open(image)
    format = img.format
    img = img.resize((int(img.width), int(img.height)), resample=Image.Resampling.LANCZOS)
    img.info['dpi'] = (72, 72)
    
    buffer = BytesIO()
    img.save(buffer, format=format)
    
    file = InMemoryUploadedFile(
        buffer,
        None,
        f"{image.name.split('.')[0]}.{format.lower()}",
        f"image/{format.lower()}",
        buffer.getbuffer().nbytes,
        None
    )
    return file


def scale_image(image, max_dimensions=(1920, 1920)):
    """
    Scale the image dimensions to fit within max_dimensions while maintaining the aspect ratio.
    """
    img = Image.open(image)
    format = img.format
    img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
    
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


def compress_image(image, max_size_kb=500):
    """
    Compress the image to ensure its size is under max_size_kb.
    """
    img = Image.open(image)
    buffer = BytesIO()
    
    target_size = max_size_kb * 1024  # Convert KB to bytes
    quality = 95  # Start with high quality
    format = "JPEG"  # Use JPEG for better compression

    # Convert to JPEG and remove alpha channel if necessary
    if img.mode in ("RGBA", "P"):  # Handle transparency
        img = img.convert("RGB")
    
    while True:
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format=format, quality=quality)
        
        if buffer.tell() <= target_size or quality <= 5:  # Stop if file size is within limits or quality is too low
            break
        
        quality -= 5  # Gradually reduce quality to compress further

    buffer.seek(0)
    file = InMemoryUploadedFile(
        buffer,
        None,
        f"{image.name.split('.')[0]}.jpeg",
        f"image/jpeg",
        buffer.tell(),
        None
    )
    return file

from django.utils.translation import get_language_from_request, activate

# --------------- [FAQ] ---------------
@login_required(login_url='login')
def faq_view(request):
    lang = get_active_language(request)
    activate(lang)
    data = {
        "faqs":  FAQ.objects.all(),
        "selected_language": lang
    }
    return render(request, "pages/cms/faq.html", data)

# Update or create FAQ
@login_required(login_url='login')
def update_faq(request):
    """FAQ aktualisieren oder neu erstellen, mit Unterstützung für Mehrsprachigkeit"""
    lang = get_active_language(request)  # Aktuelle Sprache holen

    if request.method == 'POST':
        faq_id = request.POST.get('faq_id')
        faq = get_object_or_404(FAQ, id=faq_id)

        question = request.POST.get('question')
        answer = request.POST.get('answer')
        # Dynamisch die Sprachvarianten setzen
        setattr(faq, f'question_{lang}', question)
        setattr(faq, f'answer_{lang}', answer)
        # Falls Standardsprache → auch Hauptfeld setzen
        if lang == DEFAULT_LANGUAGE:
            faq.question = question
            faq.answer = answer
        faq.save()

        return JsonResponse({'success': True})

    elif request.method == 'GET':
        new_question = request.GET.get('question')
        new_answer = request.GET.get('answer')

        # Neues FAQ mit Hauptfeld (falls Standardsprache) und Sprachfeld erstellen
        faq_data = {f'question_{lang}': new_question, f'answer_{lang}': new_answer}

        if lang == DEFAULT_LANGUAGE:
            faq_data["question"] = new_question
            faq_data["answer"] = new_answer

        faq = FAQ.objects.create(**faq_data)

        return JsonResponse({
            'id': faq.id,
            'question': getattr(faq, f'question_{lang}'),
            'answer': getattr(faq, f'answer_{lang}'),
            'order': faq.order,
            'success': True
        })

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
from django.core.paginator import Paginator

@login_required(login_url='login')
def blog_view(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "-date")  # Standard: neueste zuerst
    active_filter = request.GET.get("active", "all")

    # Nur Original-Blogs anzeigen
    blogs = Blog.objects.filter(original__isnull=True)

    if query:
        blogs = blogs.filter(title__icontains=query)

    if active_filter == "true":
        blogs = blogs.filter(active=True)
    elif active_filter == "false":
        blogs = blogs.filter(active=False)

    blogs = blogs.order_by(sort)

    paginator = Paginator(blogs, 6)  # 6 Blogs pro Seite
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "pages/cms/blog/blog.html", {
        "page_obj": page_obj,
        "blogs": page_obj.object_list,
        "query": query,
        "active_filter": active_filter,
        "sort": sort,
    })


# Delete Blog
@login_required(login_url='login')
@login_required(login_url='login')
def delete_blog(request, id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)

    blog = get_object_or_404(Blog, id=id)

    if blog.original:
        return JsonResponse({'error': 'Nur Original-Blogs dürfen gelöscht werden.'}, status=403)

    blog.delete()
    return JsonResponse({'success': True}, status=200)

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

from django.utils.text import slugify

@login_required(login_url='login')
def update_blog(request, id):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        blog = get_or_create_translated_blog(request, id)

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
            # 🧠 Slug setzen je nach Original oder Variante
            base_slug = slugify(title)
            if blog.original:
                blog.slug = f"{base_slug}-{blog.language.lower()}"
            else:
                blog.slug = base_slug
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
    lang = get_active_language(request)
    blog = get_object_or_404(Blog, id=id)

    original_blog = blog.original if blog.original else blog

    if original_blog.language != lang:
        translated_blog = original_blog.translations.filter(language=lang).first()
        if translated_blog:
            blog = translated_blog
        else:
            # Erstelle Sprachvariante durch Kopieren
            blog = Blog.objects.create(
                title=original_blog.title,
                slug=original_blog.slug + '-' + lang,
                title_image=original_blog.title_image,
                author=original_blog.author,
                body=original_blog.body,
                code=original_blog.code,
                active=False,
                description=original_blog.description,
                language=lang,
                original=original_blog,
            )


    data = {"blog": blog,"galerien": Galerie.objects.all()}

    return render(request, "pages/cms/blog/blog_update.html", data)

@login_required(login_url='login')
def blog_code(request, id):
    blog = get_or_create_translated_blog(request, id)
    return JsonResponse({"code": blog.code, "success": "true"})

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
    """Aktualisiert ein GaleryImage mit mehrsprachiger Speicherung"""
    if request.method == 'POST':
        lang = get_active_language(request)
        DEFAULT_LANGUAGE = "de"

        title = request.POST.get('title', '')

        galery_image = get_object_or_404(GaleryImage, id=id)

        if title:
            setattr(galery_image, f'title_{lang}', title)

            # Falls Standardsprache → auch Hauptfeld setzen
            if lang == DEFAULT_LANGUAGE:
                galery_image.title = title

            galery_image.save()
            return JsonResponse({"success": "Bild wurde erfolgreich gespeichert"})

        return JsonResponse({"error": "Bitte gebe einen Titel ein!"})

    return JsonResponse({"error": "Etwas ist schief gelaufen. Versuche es später nochmal"})


# Render Galery Overview
@login_required(login_url='login')
def galerien(request):
    # Per-Page sicher parsen (Default 12, max 200)
    try:
        per_page = max(1, min(200, int(request.GET.get('per_page', 12))))
    except ValueError:
        per_page = 12

    qs = Galerie.objects.all().order_by('-created_at')

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    preserved = request.GET.copy()
    preserved.pop('page', None)  # page aus Query entfernen
    querystring = preserved.urlencode()

    return render(
        request,
        "pages/cms/galery/galerien.html",
        {
            "galerien": page_obj.object_list,  # nur aktuelle Seite
            "page_obj": page_obj,
            "paginator": paginator,
            "per_page": per_page,
            "querystring": querystring,
            "total_count": paginator.count,
        },
    )

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
        lang = get_active_language(request)
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        place = request.POST.get('place', 'nothing')

        
        setattr(galery, f'title_{lang}', title)
        # Falls Standardsprache → auch Hauptfeld setzen
        if lang == DEFAULT_LANGUAGE:
            galery.title = title
        setattr(galery, f'description_{lang}', description)
        # Falls Standardsprache → auch Hauptfeld setzen
        if lang == DEFAULT_LANGUAGE:
            galery.description = description

        if place != 'nothing':
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

######################
# START SITE CONTENT #
######################

# Site Overview
@login_required(login_url='login')
def content_view(request):
    return render(request, "pages/cms/content/content.html", {})

# Main Site
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

# Main Site - Responsive Section
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

# Main Site - CMS Section
@login_required(login_url='login')
def site_view_main_cms(request):
    data = {}
    if TextContent.objects.filter(name="main_cms").exists():
        data["textContent"] = TextContent.objects.get(name='main_cms')
    if VideoFile.objects.filter(place='main_cms').exists():
        data["cmsVideo"] = VideoFile.objects.get(place='main_cms')
    return render(request, "pages/cms/content/sites/mainsite/CmsContent.html", data)

# Main Site - Price Section
@login_required(login_url='login')
def site_view_main_price(request):
    data = {"pricing_count": PricingCard.objects.count(),}
    if TextContent.objects.filter(name="main_price").exists():
        data["textContent"] = TextContent.objects.get(name='main_price')
    return render(request, "pages/cms/content/sites/mainsite/PriceContent.html", data)

# Main Site - Team Section
@login_required(login_url='login')
def site_view_main_team(request):
    data = {"member_count":  TeamMember.objects.count()}
    if TextContent.objects.filter(name="main_team").exists():
        data["textContent"] = TextContent.objects.get(name='main_team')

    return render(request, "pages/cms/content/sites/mainsite/TeamContent.html", data)

# Main Site - Know How Section
@login_required(login_url='login')
def site_view_main_know_how(request):
    data = {}
    if TextContent.objects.filter(name="main_know_how").exists():
        data["textContent"] = TextContent.objects.get(name='main_know_how')
    # Know How contents
    if TextContent.objects.filter(name="main_know_how_card_1").exists():
        data["textContentCard1"] = TextContent.objects.get(name='main_know_how_card_1')
    if TextContent.objects.filter(name="main_know_how_card_2").exists():
        data["textContentCard2"] = TextContent.objects.get(name='main_know_how_card_2')
    if TextContent.objects.filter(name="main_know_how_card_3").exists():
        data["textContentCard3"] = TextContent.objects.get(name='main_know_how_card_3')
        
    return render(request, "pages/cms/content/sites/mainsite/KnowHowContent.html", data)

# Main Site - Kunden
@login_required(login_url='login')
def site_view_main_kunden(request):
    data = {}
    if TextContent.objects.filter(name="main_kunden").exists():
        data["textContent"] = TextContent.objects.get(name='main_kunden')
    return render(request, "pages/cms/content/sites/mainsite/KundenContent.html", data)

# Main Site - FAQ
@login_required(login_url='login')
def site_view_main_faq(request):
    data = {"faq_count":  FAQ.objects.count()}
    if TextContent.objects.filter(name="main_faq").exists():
        data["textContent"] = TextContent.objects.get(name='main_faq')
    return render(request, "pages/cms/content/sites/mainsite/FAQContent.html", data)

# Kunden Site
@login_required(login_url='login')
def site_view_kunden(request):
    data = {}
    if TextContent.objects.filter(name="main_kunden").exists():
        data["textContent"] = TextContent.objects.get(name='main_kunden')
    if TextContent.objects.filter(name="main_kunden2").exists():
        data["textContent2"] = TextContent.objects.get(name='main_kunden2')
    return render(request, "pages/cms/content/sites/KundenSite.html", data)

@login_required(login_url='login')
def site_view_skills(request):
    def get_text(name):
        return TextContent.objects.get(name=name) if TextContent.objects.filter(name=name).exists() else None

    return render(request, "pages/cms/content/sites/SkillsSite.html", {
        "textContent_intro": get_text("main_skills_intro"),
        "textContent_cms": get_text("main_skills_cms"),
        "textContent_webdesign": get_text("main_skills_webdesign"),
        "textContent_logos": get_text("main_skills_logos"),
        "textContent_custom": get_text("main_skills_custom"),
    })

######################
# END SITE CONTENT   #
######################

@login_required(login_url='login')
def saveTextContent(request):
    if request.method == 'POST':
        lang = get_active_language(request)
        header = request.POST.get('header', '')
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        buttonText = request.POST.get('buttonText', '')
        # Model-Name: z.B. main_hero
        name = request.POST.get('name', '')

        customText = json.loads(request.POST.get('customText', '[]'))
        images = json.loads(request.POST.get('images', '[]'))
        galerien = json.loads(request.POST.get('galerien', '[]'))
        videos = json.loads(request.POST.get('videos', '[]'))

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

        for video in videos:
            if VideoFile.objects.filter(id=video['id']).exists():
                vid = VideoFile.objects.get(id=video['id'])
                key = video['key']
                if key:
                    if VideoFile.objects.filter(place=key).exists():
                        extra_vid = VideoFile.objects.get(place=key)
                        extra_vid.place = ""
                        extra_vid.save()
                    vid.place = key
                    vid.save()

        customKeys = []

        # Custom Text Update
        for custom in customText:
            key = custom['key']
            customKeys.append(key)
            inputs = custom['inputs']

            try:
                with transaction.atomic():
                    textContent, created = TextContent.objects.get_or_create(name=key)

                # Mehrsprachige Speicherung
                for field in ['header', 'title', 'description', 'buttonText']:
                    val = inputs.get(field, '')
                    if created or val:  # Speichere nur bei create oder wenn nicht leer
                        setattr(textContent, f'{field}_{lang}', val)

                if lang == DEFAULT_LANGUAGE:
                    for field in ['header', 'title', 'description', 'buttonText']:
                        val = inputs.get(field, '')
                        if created or val:
                            setattr(textContent, field, val)

                textContent.save()
            except IntegrityError:
                return JsonResponse({'error': f'Fehler: {key} existiert bereits'}, status=400)

        # Normal Text update
        if not name in customKeys:
            try:
                with transaction.atomic():
                    textContent, created = TextContent.objects.get_or_create(name=name)

                for field, value in [('header', header), ('title', title), ('description', description), ('buttonText', buttonText)]:
                    if created or value:
                        setattr(textContent, f'{field}_{lang}', value)

                if lang == DEFAULT_LANGUAGE:
                    for field, value in [('header', header), ('title', title), ('description', description), ('buttonText', buttonText)]:
                        if created or value:
                            setattr(textContent, field, value)

                textContent.save()

                return JsonResponse({'success': 'Element wurde erfolgreich gespeichert'}, status=200)
            except IntegrityError:
                return JsonResponse({'error': f'Fehler: {name} existiert bereits'}, status=400)

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
            'image_url': str(product.title_image.url),
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
        isOnlineAvailable = request.POST.get('isOnlineAvailable', False)
        isReduced = request.POST.get('isReduced', False)
        price_str = request.POST.get('price', '0')
        weight_str = request.POST.get('weight', '0')
        reduced_price_str = request.POST.get('reducedPrice', price_str)
        # Remove commas and convert to float
        price = float(price_str.replace(',', '.'))
        weight = float(weight_str.replace(',', '.'))
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
                discount_price=reduced_price,
                weight=weight)
            if active == "true":
                product.is_active = True
            else:
                product.is_active = False
            if isOnlineAvailable == "true":
                product.online_sell = True
            else:
                product.online_sell = False
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
            product.save()
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
        isOnlineAvailable = request.POST.get('isOnlineAvailable', False)
        isReduced = request.POST.get('isReduced', False)
        price_str = request.POST.get('price', '0')
        weight_str = request.POST.get('weight', '0')
        reduced_price_str = request.POST.get('reducedPrice', price_str)
        # Remove commas and convert to float
        price = float(price_str.replace(',', '.'))
        weight = float(weight_str.replace(',', '.'))
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
            product.weight = weight 
            product.discount_price = reduced_price

            if active == "true":
                product.is_active = True
            else:
                product.is_active = False
            if isOnlineAvailable == "true":
                product.online_sell = True
            else:
                product.online_sell = False
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
        total_revenue=Sum(F('orderitem__unit_price') * F('orderitem__quantity'), output_field=DecimalField())
    )['total_revenue'] or 0
    # Number of clients
    total_clients = Order.objects.filter(verified=True).values('buyer_email').distinct().count()

    # Open orders (not closed/paid)
    open_orders = Order.objects.filter(status='OPEN', verified=True).count()

    # Most bought products
    most_bought_products = OrderItem.objects.filter(order__status='COMPLETED').values(
    'product__title',
    'product__title_image',
).annotate(
    total_quantity=Sum('quantity'),
    total_cash=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
).order_by('-total_quantity')[:5]

    # Biggest buyers
    biggest_buyers = Order.objects.filter(verified=True).values('buyer_email').annotate(
        total_spent=Sum(F('orderitem__unit_price') * F('orderitem__quantity'), output_field=DecimalField())
    ).order_by('-total_spent')[:5]

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
@permission_classes([IsAuthenticated])
def update_order_status_admin(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    if new_status:
        old_status = order.status
        order.status = new_status
        order.save()
        sendingEmail = False
        if old_status == 'OPEN' and new_status in ['PAID', 'READY_FOR_PICKUP']:
            if new_status == 'PAID':
                send_payment_confirmation(order)
                order.paid = True
                sendingEmail = True
            elif new_status == 'READY_FOR_PICKUP':
                send_ready_for_pickup_confirmation(order)
                sendingEmail = True
            else:
                return JsonResponse({'error': f'The new status {new_status} cannot be used here'})
        else:
            if not sendingEmail:
                if old_status == 'PAID' and new_status == 'READY_FOR_PICKUP':
                    send_ready_for_pickup_confirmation(order)
                    sendingEmail = True
                elif (old_status == 'READY_FOR_PICKUP' or old_status == 'PAID' or old_status == 'OPEN') and new_status == 'SHIPPED':
                    send_shipping_confirmation(order)
                    sendingEmail = True
                else:
                    if new_status == 'PAID':
                        order.paid = True
        order.save()
        if sendingEmail:
            return Response({'success': 'Auftragsstatus wurde erfolgreich angepasst. Der Käufer hat eine Bestätiguns-Email erhalten'}, status=status.HTTP_200_OK)
        else:
            return Response({'success': 'Auftragsstatus wurde erfolgreich angepasst.'}, status=status.HTTP_200_OK)

        
    return Response({'error': 'Es wurde kein Status mitgegeben!'}, status=status.HTTP_400_BAD_REQUEST)

# views.py
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    try:
        review = Review.objects.get(pk=review_id)
        review.delete()
        return Response({'success': 'Review wurde erfolgreich gelöscht'}, status=status.HTTP_200_OK)
    except Review.DoesNotExist:
        return Response({'error': 'Bewertung nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)

# views.py
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        order.delete()
        return Response({'success': 'Auftrag wurde erfolgreich gelöscht'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Auftrag nicht gefunden'}, status=status.HTTP_404_NOT_FOUND)

# views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_by_id(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    order_serializer = OrderSerializer(order)
    
    return Response(order_serializer.data, status=status.HTTP_200_OK)

# views.py
from django.db.models import Q
from datetime import timezone, timedelta

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    
    if not product.is_active:
        return JsonResponse({'error': 'Dieses Produkt wird aktuell nicht mehr verkauft'}, status=400)
    if not product.is_in_stock:
        return JsonResponse({'error': 'Dieses Produkt ist aktuell nicht mehr im Lager verfügbar. Schauen Sie später nochmal vorbei'}, status=400)

    if not product.online_sell:
        return JsonResponse({'error': 'Dieses Produkt kann nur im Shop vor Ort erworben werden'}, status=400)


    order_id = request.session.get('order_id')
    cart_amount = request.session.get('cart_amount')
    product_amount = request.POST.get('amount')
    if not product_amount:
        return JsonResponse({'error': 'Bitte gebe die Produktanzahl (amount) an!'}, status=400)
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
    orderitem_serializer = OrderItemSerializer(order_item)
    if not created:
        order_item.quantity += int(product_amount)
        order_item.save()
        return JsonResponse({'success': f'Anzahl dieses Produkts wurde erweitert auf {order_item.quantity}', 'order_session_id': request.session['order_id'], 'order_id': order.id, 'uuid': str(order.uuid), 'order_item': orderitem_serializer.data})

    else:
        request.session['cart_amount'] = int(cart_amount) + 1
        order_item.quantity = int(product_amount)
        order_item.save()
        return JsonResponse({'success': f'Produkt wurde {product_amount}x erfolgreich zum Warenkorb hinzugefügt', 'order_session_id': request.session['order_id'], 'order_id': order.id, 'uuid': str(order.uuid), 'order_item': orderitem_serializer.data})

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def cart_items(request):
    order_id = request.session.get('order_id')
    cart_amount = request.session.get('cart_amount', 0.0)
    if not order_id:
        return JsonResponse({"error": "There is no Cart yet. Add Items to it first."})
    
    if not Order.objects.filter(id=order_id).exists():
        request.session['cart_amount'] = 0
        request.session['order_id'] = None
        return JsonResponse({"error": "Diese Order wurde gelöscht und wird jetzt zurückgesetzt."})
    
    order = Order.objects.get(id=order_id)
    total_price = 0.0
    cart_items = []
    if order:
        cart_items = [{
            'order_item_id': item.id,
            'product_title': item.product.title,
            'quantity': item.quantity,
            'price': float(item.get_price()),
            'subtotal': float(item.subtotal())
        } for item in order.orderitem_set.all()]
        total_price = float(order.total())
        return JsonResponse({'cart_items': cart_items, 'cart_amount': cart_amount, 'total_price': total_price, 'order_session_id': order_id, 'order_id': order.id})
    return JsonResponse({'error': 'There is no matching order'})


def cart_view(request):
    order_id = request.session.get('order_id')

    last_url = request.META.get('HTTP_REFERER')

    if not order_id:
        return render(request, "pages/errors/error.html", {
            "error": "Du hast noch keine Ware im Warenkorb. Füge zuerst welche hinzu.",
            "saveLink": last_url if last_url else '/'
        })
    
    if not Order.objects.filter(id=order_id).exists():
        request.session['cart_amount'] = 0
        request.session['order_id'] = None
        return render(request, "pages/errors/error.html", {
            "error": "Dein Warenkorb ist nicht mehr gültig und wurde zurückgesetzt. Bitte füge Ware erneut hinzu.",
            "saveLink": last_url if last_url else '/'
        })

    order = Order.objects.get(id=order_id)
    
    if order.verified: 
        request.session['cart_amount'] = 0
        request.session['order_id'] = None
        return render(request, "pages/errors/error.html", {
            "error": "Deine Bestellung wurde bereits verifiziert und bestellt, wodurch der Warenkorb nicht mehr valide ist. Bitte füge neue Produkte hinzu, um eine neue Bestellung zu tätigen!",
            "saveLink": last_url if last_url else '/'
        })
    context = {
        "order": order
    }
    context.update(get_opening_hours())
    
    return render(request, "pages/cms/orders/cart.html", context)


def cart_verify_success_view(request):
    context = {}
    context.update(get_opening_hours())
    return render(request, "pages/cms/orders/success/cart-verify-success.html", context)


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([])
def remove_from_cart(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    order_id = request.session.get('order_id', None)

     # Check if the OrderItem is associated with the correct Order
    if order_id and order_item.order_id == order_id:
        order_item.delete()
        cart_amount = request.session.get('cart_amount', 0)
        request.session['cart_amount'] = int(cart_amount) - 1
        return JsonResponse({'success': 'Produkt wurde erfolgreich vom Warenkorb entfernt'})
    else:
        return JsonResponse({'error': 'OrderItem does not belong to the current order'})
        
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
        # Check if the OrderItem is associated with the correct Order
    if order_id and order_item.order_id == order_id:
        # Überprüfe, ob das Produkt reduziert ist und ob die Menge nicht mehr geändert werden kann
        if order_item.product.is_reduced and not order_item.is_discounted:
            return JsonResponse({'error': 'Quantity cannot be updated for this product'})

        order_item.quantity = new_quantity
        order_item.save()
        return JsonResponse({'success': 'Quantity updated successfully'})
    else:
        return JsonResponse({'error': 'OrderItem does not belong to the current order'})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def update_cart_items(request):
    order_id = request.session.get('order_id')
    order = Order.objects.get(id=order_id) if order_id else None

    if not order:
        return JsonResponse({'error': 'Order not found in session'}, status=status.HTTP_404_NOT_FOUND)

    cart_items_data_json = request.POST.get('cart_items', '[]')
    cart_items_data = json.loads(cart_items_data_json)
    
    for item_data in cart_items_data:
        order_item_id = item_data.get('order_item_id')
        new_quantity = int(item_data.get('quantity', '0'))

        order_item = get_object_or_404(OrderItem, id=order_item_id, order=order)

        # Only update quantity if it's different from the original one
        if order_item and new_quantity is not None and new_quantity > 0 and new_quantity != order_item.quantity:
            order_item.quantity = new_quantity
            order_item.save()

    # Update total price in the session
    request.session['cart_total_price'] = float(order.total())

    cart_items = [{
        'order_item_id': item.id,
        'product_title': item.product.title,
        'quantity': item.quantity,
        'price': float(item.get_price()),
        'subtotal': float(item.subtotal())
    } for item in order.orderitem_set.all()]
    total_price = float(order.total())

    data = {
        'success': 'Der Warenkorb wurde erfolgreich aktualisiert',
        'cart_items': cart_items, 
        'tax': round(float(order.calculate_tax()), 2),
        'total_price': round(total_price, 2), 
        'total_discount': round(float(order.total_discount()), 2), 
        'total_tax_price': round(float(order.total_with_tax()), 2)
    }

    return JsonResponse(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def verify_cart(request):
    buyer_email = request.POST.get('buyer_email')
    buyer_name = request.POST.get('buyer_name')

    if not buyer_email or not buyer_name:
        return JsonResponse({'error': 'Email und Name müssen angegeben werden'}, status=400)

    order_id = request.session.get('order_id')
    
    if not order_id:
        return JsonResponse({"error": "Du hast noch keine Produkte im Einkaufswagen"})
    
    if not Order.objects.filter(id=order_id).exists():
        request.session['cart_amount'] = 0
        request.session['order_id'] = None
        return JsonResponse({"error": "Diese Order wurde gelöscht und wird jetzt zurückgesetzt."})
    
    order = Order.objects.get(id=order_id) if order_id else None

    if not order or order.status != 'OPEN' or order.verified:
        request.session['order_id'] = None  # Clear session order
        return JsonResponse({'error': 'Order ist bereits verifiziert'}, status=400)

    # Check linked prices for OrderItems
    for item in order.orderitem_set.all():
        if (item.product.is_reduced and not item.is_discounted) or (not item.product.is_reduced and item.is_discounted):
            return JsonResponse({'error': f'Falsche Preiskonfiguration {item.product.title}'}, status=400)

    # Update Order Data
    order.buyer_email = buyer_email
    # order.buyer_name = buyer_name
    order.save()

    # Generate verification link
    token = str(order.uuid)
    verification_url = request.scheme + '://' + request.get_host() + reverse('order-verify') + f'?token={token}&order_id={order_id}'
    # Send confirmation email with verification link
    user_settings = UserSettings.objects.filter(user__is_staff=False).first()
    full_name = user_settings.full_name
    company_name = user_settings.company_name
    phone_number = user_settings.tel_number
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website

    subject = f"Ihr Auftrag {order.id}"
    message = f"Hallo {buyer_name},\n\nVielen Dank für Ihren Auftrag bei {company_name}. \nIhr Auftrag mit der Auftragsnummer #{order.id} wurde erfolgreich bestätigt. \nHier sind die Details Ihres Auftrags:\n\n"

    for item in order.orderitem_set.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"
    message += f"------------------------------------------"
    message += f"\nNettopreis: {order.total_with_tax():.2f} Euro"
    message += f"\nLieferung: {order.shipping_price():.2f} Euro"
    message += f"\nUmsatzsteuer (19%): {order.calculate_tax():.2f} Euro"
    message += f"\n------------------------------------------"
    message += f"\nGesamtpreis (mit 19% Steuern): {order.total():.2f} Euro\n\n"
    message += f"\nWir haben Ihren Auftrag erhalten und benötigen noch eine Bestätigung von Ihnen, um fortzufahren. \nBitte klicken Sie auf den folgenden Link, um Ihren Auftrag zu bestätigen und zur Kasse zu gelangen:\n{verification_url}\n\n"
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
    
    request.session['cart_amount'] = 0
    request.session['order_id'] = None

    return JsonResponse({'success': 'Erfolg! Sie erhalten nun bald eine Email'})


def order_verify_view(request):
    token = request.GET.get('token')
    order_id = request.GET.get('order_id')
    last_url = request.META.get('HTTP_REFERER')
    order = get_object_or_404(Order, id=order_id, uuid=token)
    if order.verified: 
        request.session['cart_amount'] = 0
        request.session['order_id'] = None
        return render(request, "pages/errors/error.html", {
            "error": "Diese Bestellung wurde bereits verifiziert und bestellt. Für weitere Informationen überprüfe deine E-Mails oder schreibe uns eine Nachricht. Status der Bestellung: " + order.get_status_display(),
            "saveLink": last_url if last_url else '/'
        })
    context = {"order": order}
    context.update(get_opening_hours())
    return render(request, "pages/cms/orders/verify.html", context)

def order_verify_success_view(request):
    context = {}
    context.update(get_opening_hours())
    return render(request, "pages/cms/orders/success/order-verify-success.html", context)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def verify_order(request):
    orderId = request.POST.get('order_id')
    uuid = request.POST.get('token')
    address = request.POST.get('address')
    city = request.POST.get('city')
    postal_code = request.POST.get('postal_code')
    country = request.POST.get('country')
    prename = request.POST.get('buyer_prename')
    name = request.POST.get('buyer_name')
    shipping = request.POST.get('shipping')
    payment = request.POST.get('payment')
    if not orderId or not uuid:
        return JsonResponse({'error': 'orderId and uuid are required.'}, status=400)
    
    if not (address and city and postal_code and country and prename and name):
        return JsonResponse({'error': 'Die Adresse muss angegeben sein'}, status=400)

    # Check if the order exists
    order = get_object_or_404(Order, id=orderId, uuid=uuid)
    user_settings = UserSettings.objects.filter(user__is_staff=False).first()
    if not user_settings:
        return JsonResponse({'error': 'There is no staff user!'}, status=400)
    # Check if the order is not already verified
    if not order.verified:
        # Set the order as verified
        order.verified = True
        
        # Create or get the shipping address
        shipping_address, created = ShippingAddress.objects.get_or_create(
            address=address,
            city=city,
            country=country,
            prename=prename,
            name=name,
            postal_code=postal_code
        )

        # Update the order with the shipping address and shipping method
        order.buyer_address = shipping_address
        order.shipping = shipping
        order.payment = payment
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
        message = f"Vielen Dank für die Bestätigung Ihres Auftrags #{order.id} bei {company_name}.\n\n"

        for item in order.orderitem_set.all():
            message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"
        message += f"------------------------------------------"
        message += f"\nNettopreis: {order.total_with_tax():.2f} Euro"
        message += f"\nLieferung: {order.shipping_price():.2f} Euro"
        message += f"\nUmsatzsteuer (19%): {order.calculate_tax():.2f} Euro"
        message += f"\n------------------------------------------"
        message += f"\nGesamtpreis (mit 19% Steuern): {order.total():.2f} Euro\n\n"
        message += f"Ihre ausgewählte Liefermethode: {order.get_shipping_display()}"
        message += f"\nIhre ausgewählte Bezahlmethode: {order.get_payment_display()}"

        if order.payment != "CASH":
            message += "\nWir werden Ihren Auftrag so schnell wie möglich bearbeiten und Ihnen eine Rechnung zukommen lassen."
            message += "\nSobald Sie die Rechnung bezahlt haben und wir die Zahlung erhalten haben, erhalten Sie"

            if order.shipping == "PICKUP":
                message += " eine E-Mail, dass Ihre Ware zur Abholung bereit ist."
            elif order.shipping == "SHIPPING":
                message += " eine Benachrichtigung per E-Mail, sobald Ihre Bestellung versandt wurde."
        else:
            if order.shipping == "PICKUP":
                message += "\nSie erhalten eine Email, sobald Sie Ihre Bestellung abholen können."

        message += f"\n\nVielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{full_name}"
        
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
            [order.buyer_email],
            fail_silently=False,
        )

        # Email an Unternehmen
        dashboard_url = settings.DASHBOARD_URL

        subject_company = "Neue Bestellung eingegangen"
        message_company = f"Hallo {full_name},\n\nEine neue Bestellung ist eingegangen. Bitte schauen Sie im Dashboard nach, um weitere Details zu erhalten.\n\n"
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

        return JsonResponse({'success': 'Die Bestellung wurde erfolgreich aufgegeben'})
    else:
        return JsonResponse({'error': 'Order is already verified.'}, status=400)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def email_send(request):
    # Erstelle das Formular mit den POST-Daten
    form = ContactForm(request.POST)
    
    # Validierung des Formulars und reCAPTCHA
    if form.is_valid():
        name = form.cleaned_data.get('name', 'Unbekannt')
        email = form.cleaned_data.get('email')
        title = form.cleaned_data.get('title')
        message_text = form.cleaned_data.get('message')

        # Überprüfen, ob ähnliche Nachricht bereits existiert
        existing_message = Message.objects.filter(name=name, message=message_text, email=email, title=title).first()

        if existing_message:
            return Response({'error': 'Sie haben diese Nachricht bereits gesendet'}, status=status.HTTP_400_BAD_REQUEST)

        # Nachricht speichern
        message = Message.objects.create(name=name, message=message_text, email=email, title=title)

        # Email an Unternehmen senden
        subject_company = "Neue Nachricht in Ihrem CMS"
        message_company = f"Hallo Team,\n\n{name} ({email}) hat eine neue Anfrage gesendet:\n\n"
        message_company += f"Betreff: {title}\n\n"
        message_company += f"Nachricht: {message.message}\n\n"
        message_company += "Vielen Dank!\n\nMit freundlichen Grüßen,\nIhr YooLink"

        # Einstellungen für das Senden der E-Mail
        user_settings = UserSettings.objects.filter(user__is_staff=False).first()
        send_mail(
            subject_company,
            message_company,
            settings.EMAIL_HOST_USER,
            [user_settings.email],  # Add recipients if needed
            fail_silently=False,
        )

        return Response({'success': 'Ihre Nachricht wurde erfolgreich versendet.'}, status=status.HTTP_200_OK)
    else:
        # Wenn das Formular nicht gültig ist (z. B. durch ein fehlerhaftes reCAPTCHA), wird ein Fehler zurückgegeben
        return Response({'error': 'Formular-Validierung fehlgeschlagen. Bitte versuchen Sie es erneut.'}, status=status.HTTP_400_BAD_REQUEST)


# Settings
@login_required(login_url='login')
def user_settings_view(request):
    # Retrieve the UserSettings for the currently logged-in user or any specific user
    
    if not UserSettings.objects.filter(user=request.user):
        UserSettings.objects.create(
            user = request.user
        )
    
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
        user_settings.address = request.POST.get('address', '')
        user_settings.global_font = request.POST.get('global_font', '')

        # Save the updated user settings
        user_settings.save()

        return JsonResponse({'success': 'Die Einstellungen wurden erfolgreich gespeichert'})
    else:
        return JsonResponse({'error': 'Die Einstellungen konnten nicht gespeichert werden'})

@login_required(login_url='login')
def logo_settings_view(request):
    try:
        settings = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        settings = UserSettings.objects.create(user=request.user)

    return render(request, 'pages/cms/settings/profile.html', {'settings': settings})

@login_required(login_url='login')
def update_logo_favicon(request):
    user_settings = UserSettings.objects.get(user=request.user)
    updated = False

    if request.method == 'POST':
        if 'logo' in request.FILES:
            user_settings.logo = request.FILES['logo']
            updated = True
        if 'favicon' in request.FILES:
            user_settings.favicon = request.FILES['favicon']
            updated = True
        if updated:
            user_settings.save()
            return JsonResponse({'success': 'Datei erfolgreich aktualisiert'})
    return JsonResponse({'error': 'Keine Datei übermittelt'})

@login_required(login_url='login')
def delete_logo_favicon(request):
    if request.method == 'POST':
        user_settings = UserSettings.objects.get(user=request.user)
        file_type = request.POST.get('type')
        if file_type == 'logo' and user_settings.logo:
            user_settings.logo.delete(save=False)
            user_settings.logo = ''
        elif file_type == 'favicon' and user_settings.favicon:
            user_settings.favicon.delete(save=False)
            user_settings.favicon = ''
        else:
            return JsonResponse({'error': 'Ungültiger Typ oder keine Datei vorhanden'})
        user_settings.save()
        return JsonResponse({'success': f'{file_type.capitalize()} gelöscht'})
    return JsonResponse({'error': 'Ungültige Anfrage'})

"""
Opening Hours
"""

@login_required(login_url='login')
def opening_hours_view(request):
    # Retrieve the UserSettings for the currently logged-in user or any specific user

    user = User.objects.filter(is_staff=False).first()
    
    user_settings = UserSettings.objects.get(user=user) 

    for day_abbr, _ in OpeningHours.DAY_CHOICES:
        # Überprüfen, ob bereits Öffnungszeiten für diesen Tag existieren
        obj, created = OpeningHours.objects.get_or_create(user=user, day=day_abbr)
        # Wenn Objekt gerade erstellt wurde, können Sie es initialisieren, wenn nötig
        if created:
            # obj.some_field = some_value
            obj.save()

    opening_hours = OpeningHours.objects.filter(user=user)

    context = {
        'opening_hours': opening_hours,
        'settings': user_settings
        # Other context variables if needed
    }

    return render(request, 'pages/cms/openinghours/openingHours.html', context)

from django.utils import timezone as dj_timezone

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def opening_hours_update(request):
    opening_hours_data = request.POST.get('opening_hours')
    opening_hours = json.loads(opening_hours_data)
    user = User.objects.filter(is_staff=False).first()
    errors = []
    for item in opening_hours:
        day = item['day']
        is_open = bool(item['isOpen'])  # Convert to boolean
        start_time = item['startTime']
        end_time = item['endTime']
        has_lunch_break = item['hasLunchBreak']
        lunch_break_start = item['lunchBreakStart']
        lunch_break_end = item['lunchBreakEnd']
        
        if is_open and (not start_time or not end_time or not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', start_time) or not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', end_time)):
            errors.append(f"Ungültiges Format für Öffnungszeiten am {day}")
            continue
        
        # Validierung für Mittagspause
        if has_lunch_break:
            if not lunch_break_start or not lunch_break_end or not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', lunch_break_start) or not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', lunch_break_end):
                errors.append(f"Ungültiges Format für Mittagspause am {day}.")
                continue

        opening_hour = OpeningHours.objects.get(user=user, day=day)
        opening_hour.is_open = is_open
        if start_time:
            opening_hour.start_time = start_time
        if end_time:
            opening_hour.end_time = end_time
        opening_hour.has_lunch_break = has_lunch_break if has_lunch_break else False
        opening_hour.lunch_break_start = lunch_break_start if has_lunch_break else None
        opening_hour.lunch_break_end = lunch_break_end if has_lunch_break else None
        opening_hour.save()

    user_settings = UserSettings.objects.get(user=user)

    # Toggle + Text
    vacation = request.POST.get('vacation', False)
    user_settings.vacation = (str(vacation).lower() == 'true')

    lang = get_active_language(request)
    vacationText = request.POST.get('vacationText')
    if vacationText is not None:
        setattr(user_settings, f'vacationText_{lang}', vacationText)
        if lang == DEFAULT_LANGUAGE:
            user_settings.vacationText = vacationText

    # ▼ Neu: Zeitraum
    v_start_raw = request.POST.get('vacation_start')  # "YYYY-MM-DDTHH:MM" oder ""
    v_end_raw   = request.POST.get('vacation_end')

    def parse_dt_local(val):
        if not val:
            return None
        # Browser schicken mal ohne/mit Sekunden
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                naive = datetime.strptime(val, fmt)
                # <<< WICHTIG: Default-TZ, nicht current!
                tz = dj_timezone.get_default_timezone()      # i.d.R. Europe/Berlin
                return dj_timezone.make_aware(naive, tz)
            except ValueError:
                continue
        return None

    v_start = parse_dt_local(v_start_raw)
    v_end   = parse_dt_local(v_end_raw)

    # Validierung
    if v_start and v_end and v_start > v_end:
        errors.append("Urlaubsbeginn darf nicht nach dem Urlaubsende liegen.")
    else:
        user_settings.vacation_start = v_start
        user_settings.vacation_end   = v_end

    # Speichern
    try:
        user_settings.clean()
    except Exception as e:
        errors.append(str(e))

    user_settings.save()

    if errors:
        return JsonResponse({'error': 'Eine oder mehrere Öffnungszeiten konnten nicht gespeichert werden', 'errors': errors}, status=400)
    return JsonResponse({'success': 'Öffnungszeiten erfolgreich aktualisiert'})
    
@login_required(login_url='login')
def shop(request):

    data = {
        "product_count": Product.objects.count(),
        "order_count": Order.objects.filter(verified=True).count(),
        "order_not_closed_count": Order.objects.filter(verified=True).exclude(status='COMPLETED').count(),
    }
    return render(request, 'pages/cms/shop/shop.html', data)

# View to display all TeamMembers
@login_required(login_url='login')
def team_member_list(request):
    team_members = TeamMember.objects.all().order_by("display_order", "id")
    context = {
        'team_members': team_members,
    }
    return render(request, 'pages/cms/team/team.html', context)

from django.db.models import Max

# View to handle the creation of a TeamMember
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_member(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        
        # Überprüfen, ob der Name vorhanden ist
        if not full_name:
            return JsonResponse({'error': 'Voller Name ist erforderlich.'}, status=400)

        # Initialisiere optionale Felder
        active = request.POST.get('active', 'true') == "true"
        image = request.POST.get('image', '').strip()
        age = request.POST.get('age')
        email = request.POST.get('email', '').strip()
        raw_years = (request.POST.get('years_with_team') or '').strip()
        years_with_team = int(raw_years) if raw_years.isdigit() else 0
        position = request.POST.get('position', 'Mitarbeiter')
        note = request.POST.get('note', '')

        max_order = TeamMember.objects.aggregate(m=Max('display_order'))['m'] or 0
        next_order = max_order + 1

        # TeamMember erstellen
        try:
            team_member = TeamMember(
                full_name=full_name,
                active=active,
                years_with_team=years_with_team,
                position=position,
                note=note,
                display_order=next_order,
            )

            # Optionale Felder nur setzen, wenn sie vorhanden und nicht leer sind
            if image:
                team_member.image = image
            if age:
                team_member.age = int(age)
            if email:
                if TeamMember.objects.filter(email=email).exists():
                    return JsonResponse({'error': 'Diese E-Mail wird bereits verwendet.'}, status=400)
                team_member.email = email

            team_member.save()

            return JsonResponse({'success': 'Teammitglied wurde erfolgreich erstellt', 'member_id': team_member.id})
        except IntegrityError:
            return JsonResponse({'error': 'Fehler beim Erstellen des Teammitglieds, möglicherweise durch Duplikate.'}, status=400)

    return JsonResponse({'error': 'Fehler beim Erstellen vom Teammitglied'}, status=400)

@api_view(['GET'])
def get_team_member(request, id):
    team_member = get_object_or_404(TeamMember, id=id)
    return JsonResponse({
        'full_name': team_member.full_name,
        'active': team_member.active,
        'image': team_member.image,
        'age': team_member.age,
        'email': team_member.email,
        'years_with_team': team_member.years_with_team,
        'position': team_member.position,
        'note': team_member.note
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_team_member(request, id):
    team_member = get_object_or_404(TeamMember, id=id)
    data = request.data

    # E-Mail-Überprüfung auf Duplikate
    new_email = data.get('email', team_member.email).strip()
    if new_email and TeamMember.objects.filter(email=new_email).exclude(id=team_member.id).exists():
        return JsonResponse({'error': 'Diese E-Mail wird bereits verwendet.'}, status=400)

    # Felder aktualisieren
    team_member.full_name = data.get('full_name', team_member.full_name).strip()
    if not team_member.full_name:
        return JsonResponse({'error': 'Voller Name ist erforderlich.'}, status=400)

    team_member.position = data.get('position', team_member.position)
    raw_years = (data.get('years_with_team') or '').strip()
    team_member.years_with_team = int(raw_years) if raw_years.isdigit() else 0

    if 'age' in data and data['age']:
        team_member.age = int(data['age'])
    else:
        team_member.age = None

    if new_email:
        team_member.email = new_email

    team_member.note = data.get('note', team_member.note)
    
    # Active-Feld nur aktualisieren, wenn es explizit im Request vorhanden ist
    if 'active' in data:
        team_member.active = str(data['active']).lower() == "true"
    
    # Image nur aktualisieren, wenn ein nicht-leerer Wert übergeben wurde
    if data.get('image', '').strip():
        team_member.image = data['image']
    
    team_member.save()
    return JsonResponse({'success': 'Teammitglied wurde erfolgreich aktualisiert'})

@api_view(['DELETE'])
def delete_team_member(request, id):
    team_member = get_object_or_404(TeamMember, id=id)
    team_member.delete()
    return JsonResponse({'success': 'Teammitglied wurde erfolgreich gelöscht'})

from django.views.decorators.http import require_POST

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder_team_members(request):
    # akzeptiere sowohl JSON ("order":[1,2,3]) als auch Form-POST (order[]=1&order[]=2)
    order = request.data.get('order')

    if order is None:
        order = request.POST.getlist('order[]') or request.POST.getlist('order')

    if not order:
        return JsonResponse({'error': 'Keine Reihenfolge übergeben.'}, status=400)

    # ids cleanen
    try:
        ids = [int(x) for x in order]
    except Exception:
        return JsonResponse({'error': 'Ungültige ID-Liste.'}, status=400)

    # update display_order (1..n)
    for idx, member_id in enumerate(ids, start=1):
        TeamMember.objects.filter(id=member_id).update(display_order=idx)

    return JsonResponse({'success': 'Reihenfolge gespeichert'})

##################
#    PRICING     #
##################
def pricing_card_overview(request):
    cards = PricingCard.objects.select_related('button').all().order_by('order')
    return render(request, 'pages/cms/pricing/pricing.html', {
        'pricing_cards': cards
    })

from django.db import models
def create_pricing_card(request):
    if request.method == "GET":
        # Optional: Alle Buttons anzeigen, um sie im Template als Auswahl zu rendern
        buttons = Button.objects.all().order_by("order")
        return render(request, "pages/cms/pricing/pricing_create.html", {
            "buttons": buttons
        })

    elif request.method == "POST":
        data = json.loads(request.body)
        lang = get_active_language(request)

        button_id = data.get("button_id")
        button = Button.objects.filter(pk=button_id).first() if button_id else None

        card = PricingCard()
        setattr(card, f"title_{lang}", data["title"])
        setattr(card, f"description_{lang}", data.get("description", ""))

        if lang == DEFAULT_LANGUAGE:
            card.title = data["title"]
            card.description = data.get("description", "")

        card.monthly_price = data["monthly_price"]
        card.one_time_price = data["one_time_price"]
        max_order = PricingCard.objects.aggregate(models.Max("order"))["order__max"] or 0
        card.order = max_order + 1
        card.animation = data.get("animation", "fade-up")
        card.animation_delay = data.get("animation_delay", 100)
        card.button = button
        card.active = data.get("active", True)
        card.save()

        return JsonResponse({"id": card.id})

    return HttpResponseBadRequest()


def edit_pricing_card(request, pk):
    card = get_object_or_404(PricingCard, pk=pk)

    if request.method == "GET":
        buttons = Button.objects.all().order_by("order")
        return render(request, "pages/cms/pricing/pricing_edit.html", {
            "card": card,
            "buttons": buttons
        })

    elif request.method == "POST":
        data = json.loads(request.body)
        lang = get_active_language(request)

        button_id = data.get("button_id")
        button = Button.objects.filter(pk=button_id).first() if button_id else None

        setattr(card, f"title_{lang}", data["title"])
        setattr(card, f"description_{lang}", data.get("description", ""))

        if lang == DEFAULT_LANGUAGE:
            card.title = data["title"]
            card.description = data.get("description", "")

        card.monthly_price = data["monthly_price"]
        card.one_time_price = data["one_time_price"]

        card.animation = data.get("animation", "fade-up")
        card.animation_delay = data.get("animation_delay", 100)
        card.button = button
        card.active = data.get("active", True)
        card.save()

        return JsonResponse({"success": True})


    return HttpResponseBadRequest()


@csrf_exempt
def delete_pricing_card(request, pk):
    if request.method == "POST":
        card = get_object_or_404(PricingCard, pk=pk)
        card.delete()

        # Nach dem Löschen Reihenfolge aktualisieren
        cards = PricingCard.objects.order_by("order")
        for i, c in enumerate(cards):
            c.order = i
            c.save()

        return JsonResponse({"success": True})
    return HttpResponseBadRequest()

@csrf_exempt
@login_required
def pricingcard_reorder(request):
    if request.method == "POST":
        data = json.loads(request.body)
        for item in data.get("order", []):
            try:
                card = PricingCard.objects.get(id=item["id"])
                card.order = item["order"]
                card.save()
            except PricingCard.DoesNotExist:
                continue
        return JsonResponse({"success": True})
    return HttpResponseBadRequest()


def manage_features(request, pk):
    card = get_object_or_404(PricingCard, pk=pk)

    if request.method == "GET":
        features = list(card.features.order_by("order").values("id", "text"))
        return JsonResponse({"features": features})

    elif request.method == "POST":
        data = json.loads(request.body)
        lang = get_active_language(request)
        new_items = data.get("features", [])

        # IDs aus dem Request sammeln
        submitted_ids = [int(item["id"]) for item in new_items if item.get("id")]

        # Existierende Features mappen
        existing = {f.id: f for f in card.features.all()}

        # Neue Reihenfolge + Updates
        for i, item in enumerate(new_items):
            text = item["text"].strip()
            fid = item.get("id")

            if fid and int(fid) in existing:
                feature = existing[int(fid)]
            else:
                feature = PricingFeature(pricing_card=card)

            setattr(feature, f"text_{lang}", text)
            if lang == DEFAULT_LANGUAGE:
                feature.text = text

            feature.order = i
            feature.save()

            if not fid:
                submitted_ids.append(feature.id)

        # Nicht mehr vorhandene Features löschen
        if submitted_ids:
            card.features.exclude(id__in=submitted_ids).delete()

        return JsonResponse({"success": True})

    return HttpResponseBadRequest()

def button_list(request):
    buttons = Button.objects.all().order_by("order")
    return render(request, "pages/cms/buttons/button_list.html", {
        "buttons": buttons
    })

def button_create(request):
    if request.method == "GET":
        targets = [('_self', '_self'), ('_blank', '_blank'), ('_parent', '_parent'), ('_top', '_top')]
        return render(request, "pages/cms/buttons/button_create.html", {
            "targets": targets
        })

    elif request.method == "POST":
        data = json.loads(request.body)
        lang = get_active_language(request)

        button = Button()
        setattr(button, f"text_{lang}", data["text"])
        setattr(button, f"hover_text_{lang}", data.get("hover_text", ""))

        if lang == DEFAULT_LANGUAGE:
            button.text = data["text"]
            button.hover_text = data.get("hover_text", "")

        button.url = data["url"]
        button.target = data.get("target", "_self")
        button.css_classes = data.get("css_classes", "")
        button.icon = data.get("icon", "")
        button.order = data.get("order", 0)
        button.save()

        return JsonResponse({"id": button.id})


    return HttpResponseBadRequest()

def button_edit(request, pk):
    button = get_object_or_404(Button, pk=pk)

    targets = [('_self', '_self'), ('_blank', '_blank'), ('_parent', '_parent'), ('_top', '_top')]

    if request.method == "GET":
        return render(request, "pages/cms/buttons/button_edit.html", {
            "button": button,
            "targets": targets
        })

    elif request.method == "POST":
        data = json.loads(request.body)
        lang = get_active_language(request)

        setattr(button, f"text_{lang}", data["text"])
        setattr(button, f"hover_text_{lang}", data.get("hover_text", ""))

        if lang == DEFAULT_LANGUAGE:
            button.text = data["text"]
            button.hover_text = data.get("hover_text", "")

        button.url = data["url"]
        button.target = data.get("target", "_self")
        button.css_classes = data.get("css_classes", "")
        button.icon = data.get("icon", "")
        button.order = data.get("order", 0)
        button.save()

        return JsonResponse({"success": True})


    return HttpResponseBadRequest()

def button_delete(request, pk):
    if request.method == "POST":
        button = get_object_or_404(Button, pk=pk)
        button.delete()
        return JsonResponse({"success": True})
    return HttpResponseBadRequest()

# AnyFiles
@login_required(login_url='login')
def anyfile_upload_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            AnyFile.objects.create(file=uploaded_file)
            return HttpResponse('')
    return JsonResponse({'post': 'false'})

@login_required(login_url='login')
def anyfile_delete_view(request, id):
    try:
        file = AnyFile.objects.get(id=id)
        file.delete()
        return JsonResponse({"success": "Datei erfolgreich gelöscht"})
    except AnyFile.DoesNotExist:
        return JsonResponse({"error": "Datei nicht gefunden"})

@login_required(login_url='login')
def anyfile_uploader(request):
    files = AnyFile.objects.all().order_by('-id') 

    paginator = Paginator(files, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages/cms/files/anyfiles-uploader.html', {
        'files': page_obj,
        'page_obj': page_obj, 
    })

@login_required(login_url='login')
def anyfile_list_view(request):
    # Per-Page (12/24/48/96), sicher parsen
    try:
        per_page = max(1, min(200, int(request.GET.get('per_page', 24))))
    except ValueError:
        per_page = 24

    qs = AnyFile.objects.all().order_by('-id')

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    preserved = request.GET.copy()
    preserved.pop('page', None)  # page entfernen für die Links
    querystring = preserved.urlencode()

    return render(
        request,
        'pages/cms/files/anyfiles.html',
        {
            'files': page_obj.object_list,   # nur die aktuelle Seite im Grid
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'querystring': querystring,
            'total_count': paginator.count,
        }
    )

@login_required(login_url='login')
def anyfile_update_view(request, id):
    try:
        file = AnyFile.objects.get(id=id)
    except AnyFile.DoesNotExist:
        return JsonResponse({'error': 'Datei nicht gefunden'}, status=404)

    if request.method != 'POST':
        return JsonResponse({'error': 'Ungültige Methode'}, status=400)

    title = (request.POST.get('title') or '').strip()
    description = (request.POST.get('description') or '').strip()  # optional

    # aktive Sprache holen (z. B. "de", "en", …)
    lang = get_active_language(request)

    # Titel in aktueller Sprache speichern
    if title != '':
        # modeltranslation: setzt z. B. title_de / title_en
        setattr(file, f'title_{lang}', title)

        # Wenn es die Default-Sprache ist, zusätzlich das Basisfeld pflegen
        if lang == DEFAULT_LANGUAGE:
            file.title = title

    # Beschreibung ebenfalls unterstützen (falls im Form mitgegeben)
    if description != '':
        setattr(file, f'description_{lang}', description)
        if lang == DEFAULT_LANGUAGE:
            file.description = description

    file.save()

    # Für die Antwort den sprachspezifischen Wert zurückgeben
    current_title = getattr(file, f'title_{lang}', None) or file.title

    return JsonResponse({
        'success': True,
        'title': current_title,
        'lang': lang,
    })

def anyfiles_all(request):
    files = AnyFile.objects.order_by('-uploaded_at')
    data = [{
        "id": f.id,
        "url": f.file.url,
        "title": f.title or os.path.basename(f.file.name),
        "ext": os.path.splitext(f.file.name)[1].lower()
    } for f in files]
    return JsonResponse({"files": data})

# Videos
@login_required(login_url='login')
def list_videos(request):
    # Per-Page sicher parsen (Default 24, max 200)
    try:
        per_page = max(1, min(200, int(request.GET.get('per_page', 24))))
    except ValueError:
        per_page = 24

    qs = VideoFile.objects.all().order_by('-uploaded_at')

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    preserved = request.GET.copy()
    preserved.pop('page', None)  # page aus Query entfernen, damit Links sauber sind
    querystring = preserved.urlencode()

    return render(
        request,
        'pages/cms/video/video-overview.html',
        {
            'videos': page_obj.object_list,   # nur die aktuelle Seite im Grid
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'querystring': querystring,
            'total_count': paginator.count,
        }
    )

@login_required(login_url='login')
def create_video(request):
    if request.method == 'POST':
        video = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')
        subtitle = request.FILES.get('subtitle')
        # Sprache bestimmen
        lang = get_active_language(request)

        title = request.POST.get('title')
        description = request.POST.get('description', '')
        alt_text = request.POST.get('alt_text', '')
        tags = request.POST.get('tags', '')
        duration = request.POST.get('duration') or None
        # boolean fields
        is_public = request.POST.get('is_public', 'true') == 'true'
        autoplay = request.POST.get('autoplay') == 'true'
        muted = request.POST.get('muted') == 'true'
        loop = request.POST.get('loop') == 'true'
        playsinline = request.POST.get('playsinline') == 'true'
        show_controls = request.POST.get('show_controls') == 'true'
        preload = request.POST.get('preload', 'metadata')

        video_instance = VideoFile(
            file=video,
            thumbnail=thumbnail,
            subtitle_file=subtitle,
            title=title,
            description=description,
            alt_text=alt_text,
            tags=tags,
            is_public=is_public,
            duration=duration,
            autoplay=autoplay,
            muted=muted,
            loop=loop,
            playsinline=playsinline,
            show_controls=show_controls,
            preload=preload,
        )

        set_mt_fields(video_instance, lang, {
            'title': title,
            'description': description,
            'alt_text': alt_text,
            'tags': tags,
        })

        ensure_video_slug(video_instance, source_title=(title or 'video'))

        video_instance.save()
        return JsonResponse({'success': True, 'redirect': '/cms/videos/'})

    video_options = [
        ("autoplay", "Autoplay"),
        ("muted", "Stumm geschaltet"),
        ("loop", "Loop"),
        ("playsinline", "Auf Seite abspielen (Mobil)"),
        ("show_controls", "Steuerelemente anzeigen"),
    ]

    return render(request, 'pages/cms/video/video-create.html', {
        'video_options': video_options
    })


@login_required(login_url='login')
def edit_video(request, pk):
    video = get_object_or_404(VideoFile, pk=pk)

    if request.method == 'POST':
        lang = get_active_language(request)
        # sprachspezifische Meta
        set_mt_fields(video, lang, {
            'title': request.POST.get('title', ''),
            'description': request.POST.get('description', ''),
            'alt_text': request.POST.get('alt_text', ''),
            'tags': request.POST.get('tags', ''),
        })
        video.title = request.POST.get('title')
        video.description = request.POST.get('description', '')
        video.alt_text = request.POST.get('alt_text', '')
        video.tags = request.POST.get('tags', '')
        video.is_public = request.POST.get('is_public', 'true') == 'true'
        video.duration = request.POST.get('duration') or None
        video.autoplay = request.POST.get('autoplay') == 'true'
        video.muted = request.POST.get('muted') == 'true'
        video.loop = request.POST.get('loop') == 'true'
        video.playsinline = request.POST.get('playsinline') == 'true'
        video.show_controls = request.POST.get('show_controls') == 'true'
        video.preload = request.POST.get('preload', 'metadata')

        if 'file' in request.FILES:
            video.file = request.FILES['file']
        if 'thumbnail' in request.FILES:
            video.thumbnail = request.FILES['thumbnail']
        if 'subtitle' in request.FILES:
            video.subtitle_file = request.FILES['subtitle']

        if not video.slug:
            source_title = (request.POST.get('title') or video.title or 'video')
            ensure_video_slug(video, source_title)

        video.save()
        return JsonResponse({'success': True, 'redirect': '/cms/videos/'})

    options = ['autoplay', 'muted', 'loop', 'playsinline', 'show_controls']
    option_states = {opt: getattr(video, opt, False) for opt in options}
    video_options = [
        ("autoplay", "Autoplay"),
        ("muted", "Stumm geschaltet"),
        ("loop", "Loop"),
        ("playsinline", "Auf Seite abspielen (Mobil)"),
        ("show_controls", "Steuerelemente anzeigen"),
    ]

    return render(request, 'pages/cms/video/video-edit.html', {'video': video, 'video_options': video_options, 'option_states': option_states})

@login_required(login_url='login')
def delete_video(request, pk):
    video = get_object_or_404(VideoFile, pk=pk)
    video.delete()
    return JsonResponse({'success': True})

@login_required(login_url='login')
def list_all_videos(request):
    """
    Liefert alle VideoFile-Objekte als JSON für das Auswahl-Modal.
    Struktur:
      {
        "video_urls": [
          { "id": 12, "url": "...mp4", "poster": "...jpg" },
          ...
        ]
      }
    """
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    result = []
    for video in VideoFile.objects.all().order_by("-uploaded_at"):
        result.append({
            "id": video.id,
            "url": video.file.url,
            "title": video.title,
            "description": video.description or "",
            "alt_text": video.alt_text or "",
            "tags": video.tags or "",
            "duration": video.duration,
            "poster": video.thumbnail.url if video.thumbnail else static("images/designImg/filler.png"),
            "autoplay": video.autoplay,
            "muted": video.muted,
            "loop": video.loop,
            "playsinline": video.playsinline,
            "show_controls": video.show_controls,
            "preload": video.preload or "metadata"
        })

    return JsonResponse({"video_urls": result}, status=200)

@login_required(login_url='login')
def get_video_details(request, pk):
    video = get_object_or_404(VideoFile, pk=pk)

    return JsonResponse({
        "id": video.id,
        "url": video.file.url,
        "poster": video.thumbnail.url if video.thumbnail else static("images/designImg/filler.png"),
        "title": video.title,
        "description": video.description,
        "autoplay": video.autoplay,
        "muted": video.muted,
        "loop": video.loop,
        "playsinline": video.playsinline,
        "show_controls": video.show_controls,
        "preload": video.preload,
    }, status=200)


# NOTIFICATIONS
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Notification

@login_required
def notifications_list(request):
    qs = Notification.objects.latest_first().not_spam()

    # --- Filter ---
    status = request.GET.get('status', 'all')       # all | open | closed
    priority = request.GET.get('priority', 'all')   # all | low | normal | high
    per_page = request.GET.get('per_page', '10')

    try:
        per_page = max(1, min(100, int(per_page)))
    except ValueError:
        per_page = 10

    if status == 'open':
        qs = qs.filter(seen=False)
    elif status == 'closed':
        qs = qs.filter(seen=True)

    if priority in {'low', 'normal', 'high'}:
        qs = qs.filter(priority=priority)

    # --- Pagination ---
    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Querystring ohne page für Pagination-Links
    preserved = request.GET.copy()
    preserved.pop('page', None)
    querystring = preserved.urlencode()

    return render(request, 'pages/cms/notifications/notifications_list.html', {
        'notifications': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
        'filter_status': status,
        'filter_priority': priority,
        'per_page': per_page,
        'unread_count': Notification.objects.unread().count(),
    })


@login_required
def notifications_mark_all_read(request):
    if request.method != 'POST':
        return HttpResponseForbidden()
    # Nur NICHT-Spam ungelesene
    Notification.objects.unread().update(seen=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('cms:notifications-list')

@login_required
def notification_mark_read(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden()
    notification = get_object_or_404(Notification, pk=pk)
    notification.seen = True
    notification.save(update_fields=['seen'])
    return JsonResponse({'ok': True})

@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)

    # Beim Öffnen als gelesen markieren
    if not notification.seen:
        notification.seen = True
        notification.save(update_fields=['seen'])

    return render(request, 'pages/cms/notifications/notification_detail.html', {'notification': notification})

from django.views.decorators.http import require_POST

@login_required
@require_POST
def notification_delete(request, pk):
    n = get_object_or_404(Notification, pk=pk)
    n.delete()
    # Für AJAX:
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    # Fallback (nicht-AJAX)
    return redirect('cms:notifications-list')

@login_required
@require_POST
def notification_mark_spam(request, pk):
    n = get_object_or_404(Notification, pk=pk)
    n.is_spam = True
    n.seen = True  # Spam direkt als "gelesen" markieren (optional)
    n.save(update_fields=['is_spam', 'seen'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('cms:notifications-list')

@login_required
def notifications_spam_list(request):
    qs = Notification.objects.spam().latest_first()

    per_page = request.GET.get('per_page', '20')
    try:
        per_page = max(1, min(100, int(per_page)))
    except ValueError:
        per_page = 20

    paginator = Paginator(qs, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    preserved = request.GET.copy()
    preserved.pop('page', None)
    querystring = preserved.urlencode()

    return render(request, 'pages/cms/notifications/notifications_spam_list.html', {
        'notifications': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'querystring': querystring,
        'per_page': per_page,
    })

@login_required
@require_POST
def notifications_spam_delete_all(request):
    Notification.objects.spam().delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('cms:notifications-spam-list')

@login_required
@require_POST
def notification_mark_ham(request, pk):
    """
    Spam-Flag für eine Notification entfernen (zurück in die Inbox).
    """
    n = get_object_or_404(Notification, pk=pk)
    n.is_spam = False
    n.save(update_fields=['is_spam'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    # Fallback: zurück zur Spam-Liste
    return redirect('cms:notifications-spam-list')