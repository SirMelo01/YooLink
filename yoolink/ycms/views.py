from datetime import datetime
import json
import os
import re
from yoolink.forms import ContactForm
from yoolink.views import get_opening_hours
from django.shortcuts import get_object_or_404, render, redirect
from yoolink.ycms.applications.shop.models import Product
from yoolink.ycms.models import AnyFile, Button, Notification, PricingCard, PricingFeature, TeamMember, VideoFile, fileentry, OpeningHours, FAQ, UserSettings, Order, Message, Galerie, Blog, GaleryImage, TextContent, PrivacyPolicy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib import messages
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
from drf_spectacular.utils import extend_schema
from django.core.mail import send_mail
from yoolink.users.models import User
from rest_framework.permissions import IsAuthenticated
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.templatetags.static import static
from django.utils import translation
from django.utils.html import strip_tags
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from random import SystemRandom
from yoolink.ycms.tasks import send_login_2fa_email

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

    # Ensure anonymous users are redirected to the CMS login.
    if not request.user.is_authenticated:
        return redirect(reverse(settings.LOGIN_URL) + f"?next={request.path}")

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


#########################################
############ Authentication #############
#########################################

User = get_user_model()

CMS_2FA_SESSION_USER_ID = "cms_2fa_user_id"
CMS_2FA_SESSION_BACKEND = "cms_2fa_backend"
CMS_2FA_SESSION_ATTEMPTS = "cms_2fa_attempts"
CMS_2FA_MAX_ATTEMPTS = 5

def _generate_2fa_code():
    return f"{SystemRandom().randrange(0, 1000000):06d}"

def _mask_email(email):
    if not email or "@" not in email:
        return email

    local_part, domain_part = email.split("@", 1)

    if len(local_part) <= 2:
        masked_local = local_part[0] + "*" * max(len(local_part) - 1, 1)
    else:
        masked_local = local_part[:2] + "*" * (len(local_part) - 2)

    return f"{masked_local}@{domain_part}"

def _store_login_2fa_session(request, authenticated_user):
    request.session[CMS_2FA_SESSION_USER_ID] = authenticated_user.id
    request.session[CMS_2FA_SESSION_BACKEND] = authenticated_user.backend
    request.session[CMS_2FA_SESSION_ATTEMPTS] = 0


def _clear_login_2fa_session(request):
    request.session.pop(CMS_2FA_SESSION_USER_ID, None)
    request.session.pop(CMS_2FA_SESSION_BACKEND, None)
    request.session.pop(CMS_2FA_SESSION_ATTEMPTS, None)

def _issue_login_2fa_code(user_settings, user):
    email = (user_settings.email or "").strip()

    if not email:
        raise ValidationError("Für die E-Mail-2FA ist keine E-Mail-Adresse hinterlegt.")

    validate_email(email)

    code = _generate_2fa_code()
    expires_at = timezone.now() + timedelta(minutes=10)

    user_settings.two_factor_email_code = code
    user_settings.two_factor_email_code_expires_at = expires_at
    user_settings.two_factor_email_verified = False
    user_settings.save(update_fields=[
        "two_factor_email_code",
        "two_factor_email_code_expires_at",
        "two_factor_email_verified",
    ])

    try:
        send_login_2fa_email.delay(
            recipient_email=email,
            recipient_name=user_settings.full_name or user.get_username(),
            code=code,
            expires_at=expires_at.isoformat(),
        )
    except Exception as exc:
        user_settings.two_factor_email_code = ""
        user_settings.two_factor_email_code_expires_at = None
        user_settings.save(update_fields=[
            "two_factor_email_code",
            "two_factor_email_code_expires_at",
        ])
        raise RuntimeError("Die Bestätigungs-E-Mail konnte nicht vorbereitet werden.") from exc

    return code, expires_at, email

def _queue_login_2fa_for_user(user_settings, user):
    code, expires_at, email = _issue_login_2fa_code(user_settings, user)
    return code, expires_at, email

def custom_logout(request):
    _clear_login_2fa_session(request)
    logout(request)
    return redirect("ycms:login")

def Login_Cms(request):
    if request.user.is_authenticated:
        return redirect("ycms:cms")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username and not password:
            login_error = "Bitte Nutzername und Passwort eingeben."
            messages.error(request, login_error)
            return render(
                request,
                "registration/login.html",
                {
                    "currentPath": request.get_full_path(),
                    "login_error": login_error,
                    "username_value": username,
                },
            )

        if not username:
            login_error = "Bitte einen Nutzernamen eingeben."
            messages.error(request, login_error)
            return render(
                request,
                "registration/login.html",
                {
                    "currentPath": request.get_full_path(),
                    "login_error": login_error,
                    "username_value": username,
                },
            )

        if not password:
            login_error = "Bitte ein Passwort eingeben."
            messages.error(request, login_error)
            return render(
                request,
                "registration/login.html",
                {
                    "currentPath": request.get_full_path(),
                    "login_error": login_error,
                    "username_value": username,
                },
            )

        authenticated_user = authenticate(
            request,
            username=username,
            password=password,
        )

        if authenticated_user is None:
            login_error = "Benutzername oder Passwort ist ungültig."
            messages.error(request, login_error)
            return render(
                request,
                "registration/login.html",
                {
                    "currentPath": request.get_full_path(),
                    "login_error": login_error,
                    "username_value": username,
                },
            )

        user_settings = _get_user_settings(authenticated_user)

        if user_settings.two_factor_email_enabled:
            try:
                _queue_login_2fa_for_user(user_settings, authenticated_user)
            except ValidationError as exc:
                return render(
                    request,
                    "registration/login.html",
                    {
                        "currentPath": request.get_full_path(),
                        "login_error": str(exc),
                        "username_value": username,
                    },
                )
            except RuntimeError:
                return render(
                    request,
                    "registration/login.html",
                    {
                        "currentPath": request.get_full_path(),
                        "login_error": "Der Sicherheitscode konnte nicht per E-Mail versendet werden.",
                        "username_value": username,
                    },
                )

            _store_login_2fa_session(request, authenticated_user)

            return redirect("ycms:login-2fa")

        login(request, authenticated_user)
        return redirect("ycms:cms")

    return render(
        request,
        "registration/login.html",
        {
            "currentPath": request.get_full_path(),
        },
    )

def Login_Cms_2FA_Verify(request):
    pending_user_id = request.session.get(CMS_2FA_SESSION_USER_ID)
    backend = request.session.get(CMS_2FA_SESSION_BACKEND)

    if not pending_user_id or not backend:
        return redirect("ycms:login")

    try:
        pending_user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        _clear_login_2fa_session(request)
        return redirect("ycms:login")

    user_settings = _get_user_settings(pending_user)
    masked_email = _mask_email(user_settings.email)

    if request.method == "POST":
        action = request.POST.get("action", "verify")

        if action == "resend":
            try:
                _queue_login_2fa_for_user(user_settings, pending_user)
                request.session[CMS_2FA_SESSION_ATTEMPTS] = 0
                return render(
                    request,
                    "registration/login_2fa.html",
                    {
                        "masked_email": masked_email,
                        "success_message": "Ein neuer Sicherheitscode wurde versendet.",
                    },
                )
            except ValidationError as exc:
                return render(
                    request,
                    "registration/login_2fa.html",
                    {
                        "masked_email": masked_email,
                        "error_message": str(exc),
                    },
                )
            except RuntimeError:
                return render(
                    request,
                    "registration/login_2fa.html",
                    {
                        "masked_email": masked_email,
                        "error_message": "Der Sicherheitscode konnte nicht erneut versendet werden.",
                    },
                )

        entered_code = request.POST.get("code", "").strip()

        if not entered_code:
            return render(
                request,
                "registration/login_2fa.html",
                {
                    "masked_email": masked_email,
                    "error_message": "Bitte gib den Sicherheitscode ein.",
                },
            )

        if not user_settings.two_factor_email_code:
            return render(
                request,
                "registration/login_2fa.html",
                {
                    "masked_email": masked_email,
                    "error_message": "Es wurde noch kein Sicherheitscode erzeugt.",
                },
            )

        if (
            user_settings.two_factor_email_code_expires_at
            and timezone.now() > user_settings.two_factor_email_code_expires_at
        ):
            user_settings.two_factor_email_code = ""
            user_settings.two_factor_email_code_expires_at = None
            user_settings.two_factor_email_verified = False
            user_settings.save(update_fields=[
                "two_factor_email_code",
                "two_factor_email_code_expires_at",
                "two_factor_email_verified",
            ])

            return render(
                request,
                "registration/login_2fa.html",
                {
                    "masked_email": masked_email,
                    "error_message": "Der Sicherheitscode ist abgelaufen. Bitte fordere einen neuen Code an.",
                },
            )

        if entered_code != user_settings.two_factor_email_code:
            attempts = int(request.session.get(CMS_2FA_SESSION_ATTEMPTS, 0)) + 1
            request.session[CMS_2FA_SESSION_ATTEMPTS] = attempts

            if attempts >= CMS_2FA_MAX_ATTEMPTS:
                _clear_login_2fa_session(request)
                return render(
                    request,
                    "registration/login_2fa.html",
                    {
                        "masked_email": masked_email,
                        "error_message": "Zu viele Fehlversuche. Bitte melde dich erneut an.",
                    },
                )

            return render(
                request,
                "registration/login_2fa.html",
                {
                    "masked_email": masked_email,
                    "error_message": "Der eingegebene Sicherheitscode ist ungültig.",
                },
            )

        user_settings.two_factor_email_verified = True
        user_settings.two_factor_email_code = ""
        user_settings.two_factor_email_code_expires_at = None
        user_settings.save(update_fields=[
            "two_factor_email_verified",
            "two_factor_email_code",
            "two_factor_email_code_expires_at",
        ])

        login(request, pending_user, backend=backend)
        _clear_login_2fa_session(request)

        return redirect("ycms:cms")

    return render(
        request,
        "registration/login_2fa.html",
        {
            "masked_email": masked_email,
        },
    )

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
        if not my_file:
            return JsonResponse({'error': 'Keine Datei übermittelt'}, status=400)

        resized_image = resize_image(my_file)
        scaled_image = scale_image(resized_image)
        compressed_image = compress_image(scaled_image)

        image = fileentry.objects.create(file=compressed_image, title=getattr(my_file, 'name', 'Bild'))
        return JsonResponse({
            'success': 'Bild erfolgreich hochgeladen',
            'image': {
                'id': image.id,
                'url': image.file.url,
                'title': image.title,
            },
        })
    return JsonResponse({'post': 'false'})

# Delete File
@login_required(login_url='login')
def delete_file(request, id):
    if request.method != 'POST':
        return JsonResponse({"error": "Ungültige Anfrage"}, status=405)

    file = get_object_or_404(fileentry, id=id)
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

def _strip_generated_blog_intro(body, title, description):
    if not body:
        return body

    prefix = ""
    rest = body
    wrapper_match = re.match(r"^(\s*<div\b[^>]*>\s*)(.*)$", rest, flags=re.IGNORECASE | re.DOTALL)
    if wrapper_match:
        prefix = wrapper_match.group(1)
        rest = wrapper_match.group(2)

    def remove_leading_tag(html, tag_name, expected_text):
        expected_text = (expected_text or "").strip()
        if not expected_text:
            return html

        tag_match = re.match(
            rf"^\s*<{tag_name}\b[^>]*>.*?</{tag_name}>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not tag_match:
            return html

        tag_html = tag_match.group(0)
        tag_text = " ".join(strip_tags(tag_html).split())
        expected_text = " ".join(expected_text.split())
        if tag_text == expected_text:
            return html[tag_match.end():]

        return html

    rest = remove_leading_tag(rest, "h1", title)
    rest = remove_leading_tag(rest, "p", description)
    return prefix + rest

@login_required(login_url='login')
def blog_view(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "-date")  # Standard: neueste zuerst
    active_filter = request.GET.get("active", "all")
    allowed_sorts = {"-date", "date", "-last_updated", "last_updated", "title"}
    if sort not in allowed_sorts:
        sort = "-date"

    # Nur Original-Blogs anzeigen
    blogs = Blog.objects.filter(original__isnull=True).select_related("author").prefetch_related("translations")

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
    base_blogs = Blog.objects.filter(original__isnull=True)

    return render(request, "pages/cms/blog/blog.html", {
        "page_obj": page_obj,
        "blogs": page_obj.object_list,
        "query": query,
        "active_filter": active_filter,
        "sort": sort,
        "total_blog_count": base_blogs.count(),
        "active_blog_count": base_blogs.filter(active=True).count(),
        "draft_blog_count": base_blogs.filter(active=False).count(),
        "translation_count": Blog.objects.filter(original__isnull=False).count(),
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
        description = (request.POST.get('description') or '').strip()
        code = json.loads(request.POST.get('code'))
        active = request.POST.get('active', False)
        
        title_image = request.FILES.get('title_image', '')
    
        #return JsonResponse({'title': title, 'body': body, 'code': code})

        if title:
            if not description:
                return JsonResponse({'error': 'Die Beschreibung darf nicht leer sein!'}, status=400)

            body = _strip_generated_blog_intro(body, title, description)

            # Create
            blog = Blog(title=title, body=body, code=code, author=request.user)
            if active == "true":
                blog.active = True
            else:
                blog.active = False
            blog.save()
            if title_image:
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
        description = (request.POST.get('description') or '').strip()
        body = request.POST.get('body')
        code = json.loads(request.POST.get('code'))
        active = request.POST.get('active', False)
        title_image = request.FILES.get('title_image', '')

        if title:
            if not description:
                return JsonResponse({'error': 'Die Beschreibung darf nicht leer sein!'}, status=400)

            body = _strip_generated_blog_intro(body, title, description)

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
        images = fileentry.objects.all().order_by('-uploaddate')
        # Liste zur Speicherung der Bild-URLs erstellen
        image_urls = [] 

        # URLs für jedes fileentry-Objekt erstellen
        for entry in images:
            # URL für das Bild erstellen
            image_url = entry.file.url
            data = {
                "url": image_url,
                "id": entry.id,
                "title": entry.title,
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
def site_view_leistungen(request):
    logo_slot_keys = [
        "main_leistungen_logo_1",
        "main_leistungen_logo_2",
        "main_leistungen_logo_3",
        "main_leistungen_logo_4",
    ]

    def get_text(name):
        return TextContent.objects.get(name=name) if TextContent.objects.filter(name=name).exists() else None

    def get_image(place):
        return fileentry.objects.filter(place=place).first()

    legacy_logo_image = get_image("main_leistungen_logos_image")

    return render(request, "pages/cms/content/sites/LeistungenSite.html", {
        "textContent_intro": get_text("main_leistungen_intro"),
        "textContent_cms": get_text("main_leistungen_cms"),
        "textContent_webdesign": get_text("main_leistungen_webdesign"),
        "textContent_logos": get_text("main_leistungen_logos"),
        "textContent_custom": get_text("main_leistungen_custom"),
        "image_cms": get_image("main_leistungen_cms_image"),
        "image_webdesign": get_image("main_leistungen_webdesign_image"),
        "image_logo_1": get_image("main_leistungen_logo_1") or legacy_logo_image,
        "image_logo_2": get_image("main_leistungen_logo_2"),
        "image_logo_3": get_image("main_leistungen_logo_3"),
        "image_logo_4": get_image("main_leistungen_logo_4"),
        "image_custom": get_image("main_leistungen_custom_image"),
        "textContent_visitenkarten": get_text("main_leistungen_visitenkarten"),
        "image_vk_1": get_image("main_leistungen_vk_1"),
        "image_vk_2": get_image("main_leistungen_vk_2"),
        "image_vk_3": get_image("main_leistungen_vk_3"),
        "image_vk_4": get_image("main_leistungen_vk_4"),
        "textContent_medien": get_text("main_leistungen_medien"),
        "image_medien": get_image("main_leistungen_medien_image"),
    })


# views.py (CMS Content Page)
@login_required(login_url='login')
def site_view_cmsinfo(request):
    def get_text(name):
        return TextContent.objects.get(name=name) if TextContent.objects.filter(name=name).exists() else None

    return render(request, "pages/cms/content/sites/CmsInfoSite.html", {
        "textContent_hero": get_text("main_cmsinfo_hero"),
        "textContent_sec1": get_text("main_cmsinfo_sec1"),
        "textContent_sec2": get_text("main_cmsinfo_sec2"),
        "textContent_blog": get_text("main_cmsinfo_blog"),
        "textContent_blog_bullet1": get_text("main_cmsinfo_blog_bullet1"),
        "textContent_blog_bullet2": get_text("main_cmsinfo_blog_bullet2"),
        "textContent_blog_bullet3": get_text("main_cmsinfo_blog_bullet3"),
        "textContent_company": get_text("main_cmsinfo_company"),
        "textContent_company_bullet1": get_text("main_cmsinfo_company_bullet1"),
        "textContent_company_bullet2": get_text("main_cmsinfo_company_bullet2"),
        "textContent_company_bullet3": get_text("main_cmsinfo_company_bullet3"),
        "textContent_company_bullet4": get_text("main_cmsinfo_company_bullet4"),
        "textContent_trust": get_text("main_cmsinfo_trust"),

        "textContent_stat1": get_text("main_cmsinfo_stat1"),
        "textContent_stat2": get_text("main_cmsinfo_stat2"),
        "textContent_stat3": get_text("main_cmsinfo_stat3"),
        "textContent_stat4": get_text("main_cmsinfo_stat4"),

        "textContent_bottomcta": get_text("main_cmsinfo_bottomcta"),
    })


@login_required(login_url='login')
def site_view_datenschutz(request):
    policy = PrivacyPolicy.objects.first()
    owner_data = UserSettings.get_site_owner() or _get_user_settings(request.user)

    return render(
        request,
        "pages/cms/content/sites/DatenschutzSite.html",
        {
            "policy": policy,
            "owner_data": owner_data,
        },
    )

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


@login_required(login_url='login')
def save_privacy_policy(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Ungültige Anfrage'}, status=405)

    content_html = request.POST.get("content_html", "")

    owner_data = UserSettings.get_site_owner() or _get_user_settings(request.user)
    policy, _ = PrivacyPolicy.objects.get_or_create(pk=1)

    policy.use_html = True
    policy.content_html = PrivacyPolicy.prepare_content(content_html, owner_data, as_html=True)
    policy.save(update_fields=["use_html", "content_html", "updated_at"])

    return JsonResponse({'success': 'Datenschutzerklaerung wurde gespeichert'}, status=200)

@extend_schema(exclude=True)
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

#########################################
############### Settings ################
#########################################
def _get_user_settings(user):
    user_settings, _ = UserSettings.objects.get_or_create(
        user=user,
        defaults={"email": user.email or ""}
    )

    if not user_settings.email and user.email:
        user_settings.email = user.email
        user_settings.save(update_fields=["email"])

    return user_settings


def _get_site_owner_user(fallback_user):
    return User.objects.filter(is_staff=False).order_by("id").first() or fallback_user


@login_required(login_url='login')
def user_settings_view(request):
    user_settings = _get_user_settings(request.user)

    context = {
        'settings': user_settings,
    }
    return render(request, 'pages/cms/settings/settings.html', context)


@login_required(login_url='login')
def user_settings_update(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Ungültige Anfrage'}, status=405)

    user_settings = _get_user_settings(request.user)

    email = request.POST.get('email', '').strip()
    full_name = request.POST.get('full_name', '').strip()
    company_name = request.POST.get('company_name', '').strip()
    tel_number = request.POST.get('tel_number', '').strip()
    fax_number = request.POST.get('fax_number', '').strip()
    mobile_number = request.POST.get('mobile_number', '').strip()
    website = request.POST.get('website', '').strip()
    address = request.POST.get('address', '').strip()
    global_font = request.POST.get('global_font', '').strip()

    allowed_fonts = {'', 'font-sans', 'font-serif', 'font-mono'}
    if global_font not in allowed_fonts:
        global_font = 'font-sans'

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': 'Bitte gib eine gültige E-Mail-Adresse ein.'}, status=400)

    old_email = (user_settings.email or '').strip().lower()

    if user_settings.two_factor_email_enabled and not email:
        return JsonResponse(
            {'error': 'Solange die E-Mail-2FA aktiv ist, darf die E-Mail-Adresse nicht leer sein.'},
            status=400
        )

    user_settings.email = email
    user_settings.full_name = full_name
    user_settings.company_name = company_name
    user_settings.tel_number = tel_number
    user_settings.fax_number = fax_number
    user_settings.mobile_number = mobile_number
    user_settings.website = website
    user_settings.address = address
    user_settings.global_font = global_font

    two_factor_reset = (
        user_settings.two_factor_email_enabled and
        old_email != email.lower()
    )

    if two_factor_reset:
        user_settings.two_factor_email_enabled = False
        user_settings.two_factor_email_verified = False
        user_settings.two_factor_email_code = ''
        user_settings.two_factor_email_code_expires_at = None

    user_settings.save()

    if request.user.email != email:
        request.user.email = email
        request.user.save(update_fields=['email'])

    success_message = 'Die Einstellungen wurden erfolgreich gespeichert.'
    if two_factor_reset:
        success_message += ' Die E-Mail wurde geändert, daher wurde die E-Mail-2FA aus Sicherheitsgründen deaktiviert.'

    return JsonResponse({'success': success_message})


@login_required(login_url='login')
def logo_settings_view(request):
    user_settings = _get_user_settings(request.user)
    return render(request, 'pages/cms/settings/profile.html', {'settings': user_settings})


@login_required(login_url='login')
def security_settings_view(request):
    user_settings = _get_user_settings(request.user)
    return render(request, 'pages/cms/settings/security.html', {'settings': user_settings})


@login_required(login_url='login')
def update_logo_favicon(request):
    user_settings = _get_user_settings(request.user)
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

    return JsonResponse({'error': 'Keine Datei übermittelt'}, status=400)


@login_required(login_url='login')
def delete_logo_favicon(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Ungültige Anfrage'}, status=405)

    user_settings = _get_user_settings(request.user)
    file_type = request.POST.get('type')

    if file_type == 'logo' and user_settings.logo:
        user_settings.logo.delete(save=False)
        user_settings.logo = ''
    elif file_type == 'favicon' and user_settings.favicon:
        user_settings.favicon.delete(save=False)
        user_settings.favicon = ''
    else:
        return JsonResponse({'error': 'Ungültiger Typ oder keine Datei vorhanden'}, status=400)

    user_settings.save()
    return JsonResponse({'success': f'{file_type.capitalize()} gelöscht'})


@require_POST
@login_required(login_url='login')
def send_email_2fa_code(request):
    user_settings = _get_user_settings(request.user)
    email = (user_settings.email or '').strip()

    if not email:
        return JsonResponse(
            {'error': 'Bitte speichere zuerst eine E-Mail-Adresse in deinem Profil.'},
            status=400
        )

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Die hinterlegte E-Mail-Adresse ist ungültig.'}, status=400)

    try:
        _issue_login_2fa_code(user_settings, request.user)
    except ValidationError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except RuntimeError:
        return JsonResponse({'error': 'Die Bestätigungs-E-Mail konnte nicht versendet werden.'}, status=500)

    return JsonResponse({'success': f'Der Bestätigungscode wurde an {email} gesendet.'})


@require_POST
@login_required(login_url='login')
def verify_email_2fa_code(request):
    user_settings = _get_user_settings(request.user)
    code = request.POST.get('code', '').strip()

    if not code:
        return JsonResponse({'error': 'Bitte gib den Bestätigungscode ein.'}, status=400)

    if not user_settings.two_factor_email_code:
        return JsonResponse({'error': 'Es wurde noch kein Code angefordert.'}, status=400)

    if user_settings.two_factor_email_code_expires_at and timezone.now() > user_settings.two_factor_email_code_expires_at:
        user_settings.two_factor_email_code = ''
        user_settings.two_factor_email_code_expires_at = None
        user_settings.two_factor_email_verified = False
        user_settings.save(update_fields=[
            'two_factor_email_code',
            'two_factor_email_code_expires_at',
            'two_factor_email_verified',
        ])
        return JsonResponse({'error': 'Der Code ist abgelaufen. Bitte fordere einen neuen an.'}, status=400)

    if code != user_settings.two_factor_email_code:
        return JsonResponse({'error': 'Der eingegebene Code ist ungültig.'}, status=400)

    if not (user_settings.email or '').strip():
        return JsonResponse({'error': 'Für die Aktivierung muss eine E-Mail-Adresse hinterlegt sein.'}, status=400)

    user_settings.two_factor_email_enabled = True
    user_settings.two_factor_email_verified = True
    user_settings.two_factor_email_code = ''
    user_settings.two_factor_email_code_expires_at = None
    user_settings.save(update_fields=[
        'two_factor_email_enabled',
        'two_factor_email_verified',
        'two_factor_email_code',
        'two_factor_email_code_expires_at',
    ])

    return JsonResponse({'success': 'Die E-Mail-2FA wurde erfolgreich aktiviert.'})


@require_POST
@login_required(login_url='login')
def disable_email_2fa(request):
    user_settings = _get_user_settings(request.user)

    user_settings.two_factor_email_enabled = False
    user_settings.two_factor_email_verified = False
    user_settings.two_factor_email_code = ''
    user_settings.two_factor_email_code_expires_at = None
    user_settings.save(update_fields=[
        'two_factor_email_enabled',
        'two_factor_email_verified',
        'two_factor_email_code',
        'two_factor_email_code_expires_at',
    ])

    return JsonResponse({'success': 'Die E-Mail-2FA wurde deaktiviert.'})

"""
Opening Hours
"""

@login_required(login_url='login')
def opening_hours_view(request):
    # Retrieve the UserSettings for the currently logged-in user or any specific user

    user = _get_site_owner_user(request.user)
    
    user_settings = _get_user_settings(user) 

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

@extend_schema(exclude=True)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def opening_hours_update(request):
    opening_hours_data = request.POST.get('opening_hours')
    opening_hours = json.loads(opening_hours_data)
    user = _get_site_owner_user(request.user)
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

    user_settings = _get_user_settings(user)

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
@extend_schema(exclude=True)
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

@extend_schema(exclude=True)
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

@extend_schema(exclude=True)
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

@extend_schema(exclude=True)
@api_view(['DELETE'])
def delete_team_member(request, id):
    team_member = get_object_or_404(TeamMember, id=id)
    team_member.delete()
    return JsonResponse({'success': 'Teammitglied wurde erfolgreich gelöscht'})

from django.views.decorators.http import require_POST

@extend_schema(exclude=True)
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
