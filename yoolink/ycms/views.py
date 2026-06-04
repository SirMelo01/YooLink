from datetime import datetime
import json
import os
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from yoolink.forms import ContactForm
from yoolink.views import get_opening_hours
from yoolink.ycms.applications.blog.services import (
    blog_code_to_markdown,
    build_default_code_from_markdown,
    render_markdown_to_html,
)
from django.shortcuts import get_object_or_404, render, redirect
from yoolink.ycms.applications.shop.models import Order, Product
from yoolink.ycms.models import (
    FAQ,
    AnyFile,
    Blog,
    Button,
    DeveloperApiConnectAuthorization,
    DeveloperApiKey,
    GaleryImage,
    Galerie,
    Message,
    OpeningHours,
    PricingCard,
    PricingFeature,
    TeamMember,
    UserSettings,
    VideoFile,
    fileentry,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib import messages
from django.db.models import Sum, F, DecimalField
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from .forms import fileform, Blogform
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError, models, transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema
from django.core.mail import send_mail
from yoolink.users.models import User
from rest_framework.permissions import IsAuthenticated
from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from random import SystemRandom
from yoolink.ycms.tasks import send_login_2fa_email

DEFAULT_LANGUAGE = "en"
DESKTOP_IMAGE_MAX_DIMENSIONS = (1920, 1920)
MOBILE_IMAGE_MAX_DIMENSIONS = (900, 900)
DESKTOP_IMAGE_TARGET_KB = 500
MOBILE_IMAGE_TARGET_KB = 260
PNG_TO_JPEG_THRESHOLD_KB = 300



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
        markdown=original_blog.markdown,
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

        desktop_image = optimize_image_for_upload(
            my_file,
            max_dimensions=DESKTOP_IMAGE_MAX_DIMENSIONS,
            max_size_kb=DESKTOP_IMAGE_TARGET_KB,
            variant_suffix="desktop",
        )
        mobile_image = optimize_image_for_upload(
            my_file,
            max_dimensions=MOBILE_IMAGE_MAX_DIMENSIONS,
            max_size_kb=MOBILE_IMAGE_TARGET_KB,
            variant_suffix="mobile",
        )
        optimization = image_optimization_metadata(my_file, desktop_image, mobile_image)

        image = fileentry.objects.create(
            file=desktop_image,
            mobile_file=mobile_image,
            title=getattr(my_file, 'name', 'Bild'),
        )
        return JsonResponse({
            'success': 'Bild erfolgreich hochgeladen',
            'image': {
                'id': image.id,
                'url': image.file.url,
                'mobile_url': image.mobile_file_url,
                'srcset': image.responsive_srcset,
                'title': image.title,
                'format': image.file_extension,
                'has_mobile': bool(image.mobile_file),
                'optimization': optimization,
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
def generate_mobile_file(request, id):
    if request.method != 'POST':
        return JsonResponse({"error": "Ungueltige Anfrage"}, status=405)

    image = get_object_or_404(fileentry, id=id)
    if image.mobile_file:
        return JsonResponse({
            "success": "Mobile Variante ist bereits vorhanden",
            "mobile_url": image.mobile_file.url,
            "srcset": image.responsive_srcset,
            "has_mobile": True,
        })

    try:
        image.file.open("rb")
        mobile_image = optimize_image_for_upload(
            image.file,
            max_dimensions=MOBILE_IMAGE_MAX_DIMENSIONS,
            max_size_kb=MOBILE_IMAGE_TARGET_KB,
            variant_suffix="mobile",
        )
    except Exception:
        return JsonResponse(
            {"error": "Mobile Variante konnte nicht erstellt werden."},
            status=400,
        )
    finally:
        image.file.close()

    image.mobile_file.save(mobile_image.name, mobile_image, save=True)

    return JsonResponse({
        "success": "Mobile Variante wurde erstellt",
        "mobile_url": image.mobile_file.url,
        "srcset": image.responsive_srcset,
        "has_mobile": True,
        "mobile": image_variant_metadata(mobile_image),
    })


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

def image_has_alpha(img):
    return img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)


def image_upload_name(image, variant_suffix, extension):
    base_name = os.path.splitext(os.path.basename(getattr(image, "name", "image")))[0]
    safe_base = slugify(base_name) or "image"
    return f"{safe_base}_{variant_suffix}.{extension}"


def uploaded_image(buffer, image, variant_suffix, extension, content_type):
    buffer.seek(0)
    return InMemoryUploadedFile(
        buffer,
        None,
        image_upload_name(image, variant_suffix, extension),
        content_type,
        buffer.getbuffer().nbytes,
        None,
    )


def original_uploaded_image(image, variant_suffix):
    image.seek(0)
    buffer = BytesIO(image.read())
    extension = os.path.splitext(getattr(image, "name", ""))[1].lstrip(".").lower() or "jpg"
    content_type = getattr(image, "content_type", "") or f"image/{extension}"
    image.seek(0)
    return uploaded_image(buffer, image, variant_suffix, extension, content_type)


def filesize_kb(size):
    return int(round((size or 0) / 1024))


def image_variant_metadata(file_obj):
    return {
        "name": os.path.basename(file_obj.name),
        "size": file_obj.size,
        "size_kb": filesize_kb(file_obj.size),
        "format": os.path.splitext(file_obj.name)[1].lstrip(".").upper(),
    }


def normalized_image_format(img, image):
    source_format = (img.format or "").upper()
    if source_format:
        return "JPEG" if source_format == "JPG" else source_format

    extension = os.path.splitext(getattr(image, "name", ""))[1].lower()
    if extension in (".jpg", ".jpeg"):
        return "JPEG"
    if extension == ".png":
        return "PNG"
    if extension == ".webp":
        return "WEBP"
    return "JPEG"


def save_optimized_png(img, image, max_dimensions, max_size_kb, variant_suffix):
    target_size = max_size_kb * 1024
    working = img.copy()
    working.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

    if image_has_alpha(working):
        working = working.convert("RGBA")
    elif working.mode not in ("RGB", "L", "P"):
        working = working.convert("RGB")

    buffer = BytesIO()
    while True:
        buffer.seek(0)
        buffer.truncate()
        working.save(buffer, format="PNG", optimize=True)

        smallest_side = min(working.size) if working.size else 0
        if buffer.tell() <= target_size or smallest_side <= 420:
            break

        next_size = (
            max(1, int(working.width * 0.9)),
            max(1, int(working.height * 0.9)),
        )
        working = working.resize(next_size, Image.Resampling.LANCZOS)

    return uploaded_image(buffer, image, variant_suffix, "png", "image/png")


def save_optimized_lossy(img, image, max_dimensions, max_size_kb, variant_suffix, output_format):
    target_size = max_size_kb * 1024
    has_alpha = image_has_alpha(img)
    working = img.copy()
    working.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

    if output_format == "WEBP":
        extension = "webp"
        content_type = "image/webp"
        if has_alpha:
            working = working.convert("RGBA")
        else:
            working = working.convert("RGB")
    else:
        extension = "jpeg"
        content_type = "image/jpeg"
        working = working.convert("RGB")

    buffer = BytesIO()
    quality = 92
    while True:
        buffer.seek(0)
        buffer.truncate()
        save_kwargs = {"quality": quality, "optimize": True}
        if output_format == "JPEG":
            save_kwargs["progressive"] = True
        if output_format == "WEBP":
            save_kwargs["method"] = 6
        working.save(buffer, format=output_format, **save_kwargs)

        if buffer.tell() <= target_size or quality <= 55:
            break
        quality -= 7

    return uploaded_image(buffer, image, variant_suffix, extension, content_type)


def optimize_image_for_upload(
    image,
    max_dimensions=DESKTOP_IMAGE_MAX_DIMENSIONS,
    max_size_kb=DESKTOP_IMAGE_TARGET_KB,
    variant_suffix="desktop",
):
    """
    Create an optimized upload while preserving PNG transparency.
    PNG inputs stay PNG so logos and cutouts keep transparent backgrounds.
    """
    image.seek(0)
    img = Image.open(image)

    if getattr(img, "is_animated", False):
        image.seek(0)
        buffer = BytesIO(image.read())
        return uploaded_image(
            buffer,
            image,
            variant_suffix,
            os.path.splitext(image.name)[1].lstrip(".") or "gif",
            getattr(image, "content_type", "image/gif"),
        )

    source_format = normalized_image_format(img, image)
    has_alpha = image_has_alpha(img)
    should_keep_png = source_format == "PNG" and (
        has_alpha or getattr(image, "size", 0) <= PNG_TO_JPEG_THRESHOLD_KB * 1024
    )

    if should_keep_png or has_alpha:
        optimized = save_optimized_png(img, image, max_dimensions, max_size_kb, variant_suffix)
    elif source_format == "WEBP":
        optimized = save_optimized_lossy(img, image, max_dimensions, max_size_kb, variant_suffix, "WEBP")
    else:
        optimized = save_optimized_lossy(img, image, max_dimensions, max_size_kb, variant_suffix, "JPEG")

    original_size = getattr(image, "size", 0)
    original_fits_variant = img.width <= max_dimensions[0] and img.height <= max_dimensions[1]
    if original_size and original_fits_variant and optimized.size > original_size:
        optimized = original_uploaded_image(image, variant_suffix)

    image.seek(0)
    return optimized


def resize_image(image):
    return optimize_image_for_upload(image, variant_suffix="desktop")


def scale_image(image, max_dimensions=(1920, 1920)):
    return optimize_image_for_upload(image, max_dimensions=max_dimensions, variant_suffix="desktop")


def compress_image(image, max_size_kb=500):
    return optimize_image_for_upload(image, max_size_kb=max_size_kb, variant_suffix="desktop")


def image_optimization_metadata(original, desktop_image, mobile_image):
    original_size = getattr(original, "size", 0)
    desktop_saved_bytes = original_size - desktop_image.size
    mobile_saved_bytes = original_size - mobile_image.size
    desktop_saved_percent = round((desktop_saved_bytes / original_size) * 100) if original_size else 0
    mobile_saved_percent = round((mobile_saved_bytes / original_size) * 100) if original_size else 0

    original_format = os.path.splitext(getattr(original, "name", ""))[1].lstrip(".").upper()
    desktop_format = os.path.splitext(desktop_image.name)[1].lstrip(".").upper()

    note = "Bild wurde für Web und Mobil optimiert."
    if original_format == "PNG" and desktop_format == "PNG":
        note = "PNG mit Transparenz oder kleiner Dateigröße: bleibt PNG, wird verlustfrei optimiert und für Mobil verkleinert."
    elif original_format == "PNG":
        note = "PNG ohne Transparenz und großer Dateigröße: wurde als JPEG gespeichert, damit die Website schneller lädt."

    return {
        "original_size": original_size,
        "original_size_kb": filesize_kb(original_size),
        "desktop": image_variant_metadata(desktop_image),
        "mobile": image_variant_metadata(mobile_image),
        "desktop_saved_bytes": desktop_saved_bytes,
        "desktop_saved_percent": desktop_saved_percent,
        "mobile_saved_bytes": mobile_saved_bytes,
        "mobile_saved_percent": mobile_saved_percent,
        "note": note,
    }

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


def _blog_content_from_cms_request(request, title, description):
    content_source = (request.POST.get("content_source") or "").strip().lower()
    markdown_provided = "markdown" in request.POST

    if content_source == "markdown" or (markdown_provided and not request.POST.get("code")):
        markdown = (request.POST.get("markdown") or "").strip()
        if not markdown:
            return None, JsonResponse({"error": "Der Markdown-Inhalt darf nicht leer sein!"}, status=400)

        return {
            "body": render_markdown_to_html(markdown),
            "code": build_default_code_from_markdown(markdown),
            "markdown": markdown,
        }, None

    body = request.POST.get("body") or ""
    raw_code = request.POST.get("code")
    if not raw_code:
        return None, JsonResponse({"error": "Der Blog-Inhalt darf nicht leer sein!"}, status=400)

    try:
        code = json.loads(raw_code)
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "Der Blog-Inhalt konnte nicht gelesen werden."}, status=400)

    body = _strip_generated_blog_intro(body, title, description)
    markdown = blog_code_to_markdown(code, body)
    rendered_body = render_markdown_to_html(markdown) or body

    return {
        "body": rendered_body,
        "code": code,
        "markdown": markdown,
    }, None


@login_required(login_url='login')
def create_blog(request):
    if request.method == 'POST':
        # The request is a POST request
        # Retrieve POST parameters
        title = request.POST.get('title')

        if Blog.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Blog mit diesem Titel existiert bereits!'}, status=400)

        description = (request.POST.get('description') or '').strip()
        active = request.POST.get('active', False)
        
        title_image = request.FILES.get('title_image', '')
    
        #return JsonResponse({'title': title, 'body': body, 'code': code})

        if title:
            if not description:
                return JsonResponse({'error': 'Die Beschreibung darf nicht leer sein!'}, status=400)

            content_data, error_response = _blog_content_from_cms_request(request, title, description)
            if error_response:
                return error_response

            # Create
            blog = Blog(
                title=title,
                body=content_data["body"],
                markdown=content_data["markdown"],
                code=content_data["code"],
                author=request.user,
            )
            if active == "true":
                blog.active = True
            else:
                blog.active = False
            blog.save()
            if title_image:
                blog.title_image = optimize_image_for_upload(title_image)
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
        blog = get_or_create_translated_blog(request, id)

        title = request.POST.get('title')
        if blog.title != title and Blog.objects.filter(title=title).exists():
            return JsonResponse({'error': 'Ein Blog mit diesem Titel existiert bereits!'}, status=400)
        description = (request.POST.get('description') or '').strip()
        active = request.POST.get('active', False)
        title_image = request.FILES.get('title_image', '')

        if title:
            if not description:
                return JsonResponse({'error': 'Die Beschreibung darf nicht leer sein!'}, status=400)

            content_data, error_response = _blog_content_from_cms_request(request, title, description)
            if error_response:
                return error_response

            # Create
            blog.description = description
            blog.title = title
            # 🧠 Slug setzen je nach Original oder Variante
            base_slug = slugify(title)
            if blog.original:
                blog.slug = f"{base_slug}-{blog.language.lower()}"
            else:
                blog.slug = base_slug
            blog.markdown = content_data["markdown"]
            blog.body = content_data["body"]
            blog.code = content_data["code"]
            if active == "true":
                blog.active = True
            else:
                blog.active = False
            if title_image:
                blog.title_image = optimize_image_for_upload(title_image)
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
                markdown=original_blog.markdown,
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
    code = blog.code or build_default_code_from_markdown(blog.markdown)
    return JsonResponse({"code": code, "markdown": blog.markdown, "success": "true"})


@login_required(login_url='login')
def preview_blog_markdown(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=400)

    markdown = (request.POST.get("markdown") or "").strip()
    if not markdown:
        return JsonResponse({"error": "Der Markdown-Inhalt darf nicht leer sein!"}, status=400)

    return JsonResponse({
        "success": "true",
        "markdown": markdown,
        "body": render_markdown_to_html(markdown),
        "code": build_default_code_from_markdown(markdown),
    })


@login_required(login_url='login')
def convert_blog_code_to_markdown(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=400)

    raw_code = request.POST.get("code")
    if not raw_code:
        return JsonResponse({"error": "Der Blog-Inhalt darf nicht leer sein!"}, status=400)

    try:
        code = json.loads(raw_code)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Der Blog-Inhalt konnte nicht gelesen werden."}, status=400)

    markdown = blog_code_to_markdown(code)
    return JsonResponse({
        "success": "true",
        "markdown": markdown,
        "body": render_markdown_to_html(markdown),
    })

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
        optimized_image = optimize_image_for_upload(my_file)
        doc = GaleryImage.objects.create(upload=optimized_image)
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
                "mobile_url": entry.mobile_file_url,
                "srcset": entry.responsive_srcset,
                "id": entry.id,
                "title": entry.title,
                "format": entry.file_extension,
                "has_mobile": bool(entry.mobile_file),
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


def _parse_developer_key_expiry(request):
    expires_in = request.POST.get("expires_in", "never")

    if expires_in == "never":
        return None, ""

    if expires_in == "custom":
        raw_value = (request.POST.get("custom_expires_at") or "").strip()
        if not raw_value:
            return None, "Bitte gib ein Ablaufdatum an."

        for date_format in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                naive = datetime.strptime(raw_value, date_format)
                expires_at = timezone.make_aware(naive, timezone.get_default_timezone())
                break
            except ValueError:
                expires_at = None

        if not expires_at:
            return None, "Das Ablaufdatum ist ungültig."

        if expires_at <= timezone.now():
            return None, "Das Ablaufdatum muss in der Zukunft liegen."

        return expires_at, ""

    allowed_days = {"30": 30, "90": 90, "365": 365}
    days = allowed_days.get(expires_in)
    if not days:
        return None, "Die ausgewählte Laufzeit ist ungültig."

    return timezone.now() + timedelta(days=days), ""


@login_required(login_url='login')
def developer_settings_view(request):
    generated_api_key = ""

    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "revoke":
            api_key = get_object_or_404(
                DeveloperApiKey,
                id=request.POST.get("key_id"),
                created_by=request.user,
            )
            api_key.revoke()
            messages.success(request, "Der API-Key wurde widerrufen.")
            return redirect("ycms:developer-settings")

        name = (request.POST.get("name") or "").strip()
        access_level = request.POST.get("access_level", DeveloperApiKey.READ)
        allowed_apps = request.POST.getlist("allowed_apps")
        valid_access_levels = {choice[0] for choice in DeveloperApiKey.ACCESS_LEVEL_CHOICES}
        valid_apps = {choice[0] for choice in DeveloperApiKey.APP_CHOICES}
        allowed_apps = [app for app in allowed_apps if app in valid_apps]

        expires_at, expiry_error = _parse_developer_key_expiry(request)

        if not name:
            messages.error(request, "Bitte gib dem API-Key einen Namen.")
        elif access_level not in valid_access_levels:
            messages.error(request, "Die Berechtigungsstufe ist ungültig.")
        elif not allowed_apps:
            messages.error(request, "Bitte wähle mindestens eine App aus.")
        elif expiry_error:
            messages.error(request, expiry_error)
        else:
            _, generated_api_key = DeveloperApiKey.issue_key(
                created_by=request.user,
                name=name,
                access_level=access_level,
                allowed_apps=allowed_apps,
                expires_at=expires_at,
            )
            messages.success(request, "Der API-Key wurde erstellt. Kopiere ihn jetzt, er wird später nicht erneut angezeigt.")

    all_api_keys = DeveloperApiKey.objects.filter(created_by=request.user)
    api_keys = [api_key for api_key in all_api_keys if not api_key.is_revoked()]
    revoked_api_keys = [api_key for api_key in all_api_keys if api_key.is_revoked()]
    active_keys_count = sum(1 for api_key in api_keys if api_key.is_usable())
    api_base_url = request.build_absolute_uri("/api/cms/")
    blog_api_url = request.build_absolute_uri("/api/cms/blog/")
    api_ping_url = request.build_absolute_uri("/api/ping/")
    api_connect_authorize_url = request.build_absolute_uri(reverse("ycms:developer-connect"))
    api_connect_token_url = request.build_absolute_uri(reverse("api:developer-connect-token"))
    api_docs_url = request.build_absolute_uri(reverse("api-docs"))
    api_schema_url = request.build_absolute_uri(reverse("api-schema"))

    return render(
        request,
        "pages/cms/settings/developer.html",
        {
            "api_keys": api_keys,
            "revoked_api_keys": revoked_api_keys,
            "active_keys_count": active_keys_count,
            "app_choices": DeveloperApiKey.APP_CHOICES,
            "access_level_choices": DeveloperApiKey.ACCESS_LEVEL_CHOICES,
            "generated_api_key": generated_api_key,
            "api_base_url": api_base_url,
            "blog_api_url": blog_api_url,
            "api_ping_url": api_ping_url,
            "api_connect_authorize_url": api_connect_authorize_url,
            "api_connect_token_url": api_connect_token_url,
            "api_docs_url": api_docs_url,
            "api_schema_url": api_schema_url,
        },
    )


@login_required(login_url='login')
def developer_api_docs_view(request):
    return render(
        request,
        "pages/cms/settings/developer_api_docs.html",
        {
            "api_base_url": request.build_absolute_uri("/api/cms/"),
            "blog_api_url": request.build_absolute_uri("/api/cms/blog/"),
            "api_ping_url": request.build_absolute_uri("/api/ping/"),
            "api_connect_authorize_url": request.build_absolute_uri(reverse("ycms:developer-connect")),
            "api_connect_token_url": request.build_absolute_uri(reverse("api:developer-connect-token")),
            "api_docs_url": request.build_absolute_uri(reverse("api-docs")),
            "api_schema_url": request.build_absolute_uri(reverse("api-schema")),
        },
    )


def _connect_error_redirect(redirect_uri, *, error, error_description="", state=""):
    params = {"error": error}
    if error_description:
        params["error_description"] = error_description
    if state:
        params["state"] = state
    return _connect_redirect(redirect_uri, params)


def _connect_redirect(redirect_uri, params):
    parsed = urlparse(redirect_uri)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    query.extend((key, value) for key, value in params.items() if value)
    return urlunparse(parsed._replace(query=urlencode(query)))


def _validate_connect_redirect_uri(redirect_uri):
    if not redirect_uri:
        return "redirect_uri fehlt."

    parsed = urlparse(redirect_uri)
    if parsed.fragment:
        return "redirect_uri darf keinen Fragment-Teil enthalten."

    if parsed.scheme == "https" and parsed.netloc:
        return ""

    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if settings.DEBUG and parsed.scheme == "http" and parsed.hostname in local_hosts:
        return ""

    return "redirect_uri muss eine HTTPS-URL sein. Im DEBUG-Modus ist localhost per HTTP erlaubt."


def _parse_connect_apps(raw_apps):
    raw_apps = raw_apps or DeveloperApiKey.APP_BLOG
    values = [value.strip().lower() for value in re.split(r"[\s,]+", raw_apps) if value.strip()]
    normalized = []
    valid_apps = {choice[0] for choice in DeveloperApiKey.APP_CHOICES}

    for value in values:
        if value == DeveloperApiKey.LEGACY_APP_BLOGS:
            value = DeveloperApiKey.APP_BLOG
        if value not in valid_apps:
            return [], f"Unbekannter App Scope: {value}"
        normalized.append(value)

    return sorted(set(normalized or [DeveloperApiKey.APP_BLOG])), ""


def _get_connect_context(request):
    source = request.POST if request.method == "POST" else request.GET
    raw_apps = source.get("scope") or source.get("apps") or DeveloperApiKey.APP_BLOG
    allowed_apps, apps_error = _parse_connect_apps(raw_apps)
    access_level = source.get("access_level") or DeveloperApiKey.READ
    redirect_uri = (source.get("redirect_uri") or "").strip()
    code_challenge_method = (source.get("code_challenge_method") or DeveloperApiConnectAuthorization.METHOD_S256).strip()
    client_name = (source.get("client_name") or source.get("client_id") or "Externe Anwendung").strip()[:160]

    errors = []
    redirect_error = _validate_connect_redirect_uri(redirect_uri)
    if redirect_error:
        errors.append(redirect_error)
    if apps_error:
        errors.append(apps_error)
    if access_level not in {choice[0] for choice in DeveloperApiKey.ACCESS_LEVEL_CHOICES}:
        errors.append("access_level muss read oder write sein.")
    if not source.get("code_challenge"):
        errors.append("code_challenge fehlt.")
    if code_challenge_method != DeveloperApiConnectAuthorization.METHOD_S256:
        errors.append("code_challenge_method muss S256 sein.")

    params = {
        "client_name": client_name,
        "redirect_uri": redirect_uri,
        "state": (source.get("state") or "").strip(),
        "code_challenge": (source.get("code_challenge") or "").strip(),
        "code_challenge_method": code_challenge_method,
        "access_level": access_level,
        "scope": " ".join(allowed_apps or [DeveloperApiKey.APP_BLOG]),
    }

    return {
        "errors": errors,
        "connect_params": params,
        "allowed_apps": allowed_apps,
        "access_level_label": dict(DeveloperApiKey.ACCESS_LEVEL_CHOICES).get(access_level, access_level),
        "app_labels": [dict(DeveloperApiKey.APP_CHOICES).get(app, app) for app in allowed_apps],
    }


@login_required(login_url='login')
def developer_connect_view(request):
    context = _get_connect_context(request)
    params = context["connect_params"]

    if request.method == "POST" and request.POST.get("action") == "deny" and params["redirect_uri"]:
        return redirect(
            _connect_error_redirect(
                params["redirect_uri"],
                error="access_denied",
                error_description="Der YooLink Benutzer hat die Verbindung abgelehnt.",
                state=params["state"],
            )
        )

    if context["errors"]:
        return render(request, "pages/cms/settings/developer_connect.html", context, status=400)

    if request.method == "POST":
        _, raw_code = DeveloperApiConnectAuthorization.issue_code(
            created_by=request.user,
            client_name=params["client_name"],
            redirect_uri=params["redirect_uri"],
            state=params["state"],
            code_challenge=params["code_challenge"],
            code_challenge_method=params["code_challenge_method"],
            access_level=params["access_level"],
            allowed_apps=context["allowed_apps"],
        )
        return redirect(_connect_redirect(params["redirect_uri"], {"code": raw_code, "state": params["state"]}))

    return render(request, "pages/cms/settings/developer_connect.html", context)


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
@login_required(login_url='login')
def pricing_card_overview(request):
    cards = PricingCard.objects.select_related('button').all().order_by('order')
    return render(request, 'pages/cms/pricing/pricing.html', {
        'pricing_cards': cards
    })

@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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

@login_required(login_url='login')
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


@login_required(login_url='login')
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

@login_required(login_url='login')
def button_list(request):
    buttons = Button.objects.all().order_by("order")
    return render(request, "pages/cms/buttons/button_list.html", {
        "buttons": buttons
    })

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
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
        "description": video.description or "",
        "alt_text": video.alt_text or "",
        "tags": video.tags or "",
        "duration": video.duration,
        "autoplay": video.autoplay,
        "muted": video.muted,
        "loop": video.loop,
        "playsinline": video.playsinline,
        "show_controls": video.show_controls,
        "preload": video.preload,
    }, status=200)

