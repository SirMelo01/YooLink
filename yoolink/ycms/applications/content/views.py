import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import activate, get_language_from_request

from yoolink.ycms.models import FAQ, Galerie, PricingCard, TeamMember, UserSettings, VideoFile, fileentry

from .models import PrivacyPolicy, TextContent

DEFAULT_LANGUAGE = "en"


def get_active_language(request):
    lang = get_language_from_request(request)
    available_languages = dict(settings.LANGUAGES)

    if lang not in available_languages:
        lang = DEFAULT_LANGUAGE

    activate(lang)
    return lang


def _get_user_settings(user):
    user_settings, _ = UserSettings.objects.get_or_create(
        user=user,
        defaults={"email": user.email or ""},
    )

    if not user_settings.email and user.email:
        user_settings.email = user.email
        user_settings.save(update_fields=["email"])

    return user_settings


def _get_text(name):
    return TextContent.objects.filter(name=name).first()


def _get_image(place):
    return fileentry.objects.filter(place=place).first()


@login_required(login_url="login")
def content_view(request):
    return render(request, "pages/cms/content/content.html", {})


@login_required(login_url="login")
def site_view_main(request):
    return render(request, "pages/cms/content/sites/MainSite.html", {})


@login_required(login_url="login")
def site_view_main_hero(request):
    data = {}
    text_content = _get_text("main_hero")
    if text_content:
        data["textContent"] = text_content
    if Galerie.objects.filter(place="main_hero").exists():
        data["heroImages"] = Galerie.objects.get(place="main_hero").images.all()
    return render(request, "pages/cms/content/sites/mainsite/HeroContent.html", data)


@login_required(login_url="login")
def site_view_main_responsive(request):
    data = {}
    text_content = _get_text("main_responsive")
    if text_content:
        data["textContent"] = text_content

    if Galerie.objects.filter(place="main_responsive_desktop").exists():
        data["responsiveDesktopImages"] = Galerie.objects.get(place="main_responsive_desktop").images.all()

    if Galerie.objects.filter(place="main_responsive_handy").exists():
        data["responsiveHandyImages"] = Galerie.objects.get(place="main_responsive_handy").images.all()

    return render(request, "pages/cms/content/sites/mainsite/ResponsiveContent.html", data)


@login_required(login_url="login")
def site_view_main_cms(request):
    data = {}
    text_content = _get_text("main_cms")
    if text_content:
        data["textContent"] = text_content
    if VideoFile.objects.filter(place="main_cms").exists():
        data["cmsVideo"] = VideoFile.objects.get(place="main_cms")
    return render(request, "pages/cms/content/sites/mainsite/CmsContent.html", data)


@login_required(login_url="login")
def site_view_main_price(request):
    data = {"pricing_count": PricingCard.objects.count()}
    text_content = _get_text("main_price")
    if text_content:
        data["textContent"] = text_content
    return render(request, "pages/cms/content/sites/mainsite/PriceContent.html", data)


@login_required(login_url="login")
def site_view_main_team(request):
    data = {"member_count": TeamMember.objects.count()}
    text_content = _get_text("main_team")
    if text_content:
        data["textContent"] = text_content
    return render(request, "pages/cms/content/sites/mainsite/TeamContent.html", data)


@login_required(login_url="login")
def site_view_main_know_how(request):
    data = {}
    text_content = _get_text("main_know_how")
    if text_content:
        data["textContent"] = text_content

    for index in range(1, 4):
        card_content = _get_text(f"main_know_how_card_{index}")
        if card_content:
            data[f"textContentCard{index}"] = card_content

    return render(request, "pages/cms/content/sites/mainsite/KnowHowContent.html", data)


@login_required(login_url="login")
def site_view_main_kunden(request):
    data = {}
    text_content = _get_text("main_kunden")
    if text_content:
        data["textContent"] = text_content
    return render(request, "pages/cms/content/sites/mainsite/KundenContent.html", data)


@login_required(login_url="login")
def site_view_main_faq(request):
    data = {"faq_count": FAQ.objects.count()}
    text_content = _get_text("main_faq")
    if text_content:
        data["textContent"] = text_content
    return render(request, "pages/cms/content/sites/mainsite/FAQContent.html", data)


@login_required(login_url="login")
def site_view_kunden(request):
    data = {}
    text_content = _get_text("main_kunden")
    if text_content:
        data["textContent"] = text_content
    text_content2 = _get_text("main_kunden2")
    if text_content2:
        data["textContent2"] = text_content2
    return render(request, "pages/cms/content/sites/KundenSite.html", data)


@login_required(login_url="login")
def site_view_leistungen(request):
    legacy_logo_image = _get_image("main_leistungen_logos_image")

    return render(
        request,
        "pages/cms/content/sites/LeistungenSite.html",
        {
            "textContent_intro": _get_text("main_leistungen_intro"),
            "textContent_cms": _get_text("main_leistungen_cms"),
            "textContent_webdesign": _get_text("main_leistungen_webdesign"),
            "textContent_logos": _get_text("main_leistungen_logos"),
            "textContent_custom": _get_text("main_leistungen_custom"),
            "image_cms": _get_image("main_leistungen_cms_image"),
            "image_webdesign": _get_image("main_leistungen_webdesign_image"),
            "image_logo_1": _get_image("main_leistungen_logo_1") or legacy_logo_image,
            "image_logo_2": _get_image("main_leistungen_logo_2"),
            "image_logo_3": _get_image("main_leistungen_logo_3"),
            "image_logo_4": _get_image("main_leistungen_logo_4"),
            "image_custom": _get_image("main_leistungen_custom_image"),
            "textContent_visitenkarten": _get_text("main_leistungen_visitenkarten"),
            "image_vk_1": _get_image("main_leistungen_vk_1"),
            "image_vk_2": _get_image("main_leistungen_vk_2"),
            "image_vk_3": _get_image("main_leistungen_vk_3"),
            "image_vk_4": _get_image("main_leistungen_vk_4"),
            "textContent_medien": _get_text("main_leistungen_medien"),
            "image_medien": _get_image("main_leistungen_medien_image"),
        },
    )


@login_required(login_url="login")
def site_view_cmsinfo(request):
    return render(
        request,
        "pages/cms/content/sites/CmsInfoSite.html",
        {
            "textContent_hero": _get_text("main_cmsinfo_hero"),
            "textContent_sec1": _get_text("main_cmsinfo_sec1"),
            "textContent_sec2": _get_text("main_cmsinfo_sec2"),
            "textContent_blog": _get_text("main_cmsinfo_blog"),
            "textContent_blog_bullet1": _get_text("main_cmsinfo_blog_bullet1"),
            "textContent_blog_bullet2": _get_text("main_cmsinfo_blog_bullet2"),
            "textContent_blog_bullet3": _get_text("main_cmsinfo_blog_bullet3"),
            "textContent_company": _get_text("main_cmsinfo_company"),
            "textContent_company_bullet1": _get_text("main_cmsinfo_company_bullet1"),
            "textContent_company_bullet2": _get_text("main_cmsinfo_company_bullet2"),
            "textContent_company_bullet3": _get_text("main_cmsinfo_company_bullet3"),
            "textContent_company_bullet4": _get_text("main_cmsinfo_company_bullet4"),
            "textContent_trust": _get_text("main_cmsinfo_trust"),
            "textContent_stat1": _get_text("main_cmsinfo_stat1"),
            "textContent_stat2": _get_text("main_cmsinfo_stat2"),
            "textContent_stat3": _get_text("main_cmsinfo_stat3"),
            "textContent_stat4": _get_text("main_cmsinfo_stat4"),
            "textContent_bottomcta": _get_text("main_cmsinfo_bottomcta"),
            "image_sec1_card_1": _get_image("main_cmsinfo_sec1_card_1"),
            "image_sec1_card_2": _get_image("main_cmsinfo_sec1_card_2"),
            "image_sec1_card_3": _get_image("main_cmsinfo_sec1_card_3"),
            "image_sec1_card_4": _get_image("main_cmsinfo_sec1_card_4"),
            "image_sec1_preview_1": _get_image("main_cmsinfo_sec1_preview_1"),
            "image_sec1_preview_2": _get_image("main_cmsinfo_sec1_preview_2"),
            "image_sec1_preview_3": _get_image("main_cmsinfo_sec1_preview_3"),
            "image_sec1_preview_4": _get_image("main_cmsinfo_sec1_preview_4"),
            "image_sec2_card_1": _get_image("main_cmsinfo_sec2_card_1"),
            "image_sec2_card_2": _get_image("main_cmsinfo_sec2_card_2"),
            "image_sec2_card_3": _get_image("main_cmsinfo_sec2_card_3"),
            "image_sec2_preview_1": _get_image("main_cmsinfo_sec2_preview_1"),
            "image_sec2_preview_2": _get_image("main_cmsinfo_sec2_preview_2"),
            "image_sec2_preview_3": _get_image("main_cmsinfo_sec2_preview_3"),
            "image_blog": _get_image("main_cmsinfo_blog_image"),
            "image_company": _get_image("main_cmsinfo_company_image"),
        },
    )


@login_required(login_url="login")
def site_view_logos(request):
    return render(
        request,
        "pages/cms/content/sites/LogosSite.html",
        {
            "textContent_hero": _get_text("main_logos_hero"),
            "textContent_hero_secondary": _get_text("main_logos_hero_secondary"),
            "image_hero_logo_1": _get_image("main_logos_hero_logo_1"),
            "image_hero_logo_2": _get_image("main_logos_hero_logo_2"),
            "image_hero_logo_3": _get_image("main_logos_hero_logo_3"),
            "image_hero_logo_4": _get_image("main_logos_hero_logo_4"),
            "image_hero_logo_5": _get_image("main_logos_hero_logo_5"),
            "textContent_warum": _get_text("main_logos_warum"),
            "textContent_warum_card1": _get_text("main_logos_warum_card1"),
            "textContent_warum_card2": _get_text("main_logos_warum_card2"),
            "textContent_warum_card3": _get_text("main_logos_warum_card3"),
            "textContent_leistungen": _get_text("main_logos_leistungen"),
            "textContent_leistungen_card1": _get_text("main_logos_leistungen_card1"),
            "textContent_leistungen_card1_bullet1": _get_text("main_logos_leistungen_card1_bullet1"),
            "textContent_leistungen_card1_bullet2": _get_text("main_logos_leistungen_card1_bullet2"),
            "textContent_leistungen_card1_bullet3": _get_text("main_logos_leistungen_card1_bullet3"),
            "textContent_leistungen_card2": _get_text("main_logos_leistungen_card2"),
            "textContent_leistungen_card2_bullet1": _get_text("main_logos_leistungen_card2_bullet1"),
            "textContent_leistungen_card2_bullet2": _get_text("main_logos_leistungen_card2_bullet2"),
            "textContent_leistungen_card2_bullet3": _get_text("main_logos_leistungen_card2_bullet3"),
            "textContent_leistungen_card3": _get_text("main_logos_leistungen_card3"),
            "textContent_leistungen_card3_bullet1": _get_text("main_logos_leistungen_card3_bullet1"),
            "textContent_leistungen_card3_bullet2": _get_text("main_logos_leistungen_card3_bullet2"),
            "textContent_leistungen_card3_bullet3": _get_text("main_logos_leistungen_card3_bullet3"),
            "textContent_leistungen_premium": _get_text("main_logos_leistungen_premium"),
            "textContent_leistungen_premium_bullet1": _get_text("main_logos_leistungen_premium_bullet1"),
            "textContent_leistungen_premium_bullet2": _get_text("main_logos_leistungen_premium_bullet2"),
            "textContent_leistungen_premium_bullet3": _get_text("main_logos_leistungen_premium_bullet3"),
            "textContent_leistungen_premium_bullet4": _get_text("main_logos_leistungen_premium_bullet4"),
            "textContent_premium": _get_text("main_logos_premium"),
            "textContent_premium_bullet1": _get_text("main_logos_premium_bullet1"),
            "textContent_premium_bullet2": _get_text("main_logos_premium_bullet2"),
            "textContent_premium_bullet3": _get_text("main_logos_premium_bullet3"),
            "textContent_prozess": _get_text("main_logos_prozess"),
            "textContent_prozess_step1": _get_text("main_logos_prozess_step1"),
            "textContent_prozess_step2": _get_text("main_logos_prozess_step2"),
            "textContent_prozess_step3": _get_text("main_logos_prozess_step3"),
            "textContent_prozess_step4": _get_text("main_logos_prozess_step4"),
            "textContent_prozess_step5": _get_text("main_logos_prozess_step5"),
            "textContent_lieferumfang": _get_text("main_logos_lieferumfang"),
            "textContent_lieferumfang_bullet1": _get_text("main_logos_lieferumfang_bullet1"),
            "textContent_lieferumfang_bullet2": _get_text("main_logos_lieferumfang_bullet2"),
            "textContent_lieferumfang_bullet3": _get_text("main_logos_lieferumfang_bullet3"),
            "textContent_lieferumfang_bullet4": _get_text("main_logos_lieferumfang_bullet4"),
            "textContent_lieferumfang_bullet5": _get_text("main_logos_lieferumfang_bullet5"),
            "textContent_usp": _get_text("main_logos_usp"),
            "textContent_usp_card1": _get_text("main_logos_usp_card1"),
            "textContent_usp_card2": _get_text("main_logos_usp_card2"),
            "textContent_usp_card3": _get_text("main_logos_usp_card3"),
            "textContent_bottomcta": _get_text("main_logos_bottomcta"),
        },
    )


@login_required(login_url="login")
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


@login_required(login_url="login")
def save_text_content(request):
    if request.method != "POST":
        return JsonResponse({"error": "Etwas ist falsch gelaufen. Versuche es spÃ¤ter nochmal"}, status=400)

    lang = get_active_language(request)
    name = request.POST.get("name", "")

    custom_text = json.loads(request.POST.get("customText", "[]"))
    images = json.loads(request.POST.get("images", "[]"))
    galerien = json.loads(request.POST.get("galerien", "[]"))
    videos = json.loads(request.POST.get("videos", "[]"))

    _assign_image_slots(images)
    _assign_gallery_slots(galerien)
    _assign_video_slots(videos)

    custom_keys = []
    for custom in custom_text:
        key = custom["key"]
        custom_keys.append(key)
        result = _save_text_values(key, custom["inputs"], lang)
        if result is not None:
            return result

    if name not in custom_keys:
        values = {
            "header": request.POST.get("header", ""),
            "title": request.POST.get("title", ""),
            "description": request.POST.get("description", ""),
            "buttonText": request.POST.get("buttonText", ""),
        }
        result = _save_text_values(name, values, lang)
        if result is not None:
            return result
        return JsonResponse({"success": "Element wurde erfolgreich gespeichert"}, status=200)

    return JsonResponse({"success": "Elemente wurden erfolgreich gespeichert"}, status=200)


def _assign_image_slots(images):
    for image in images:
        if fileentry.objects.filter(id=image["id"]).exists():
            file = fileentry.objects.get(id=image["id"])
            key = image["key"]
            if key:
                if fileentry.objects.filter(place=key).exists():
                    extra = fileentry.objects.get(place=key)
                    extra.place = "nothing"
                    extra.save()
                file.place = key
                file.save()


def _assign_gallery_slots(galerien):
    for galery in galerien:
        if Galerie.objects.filter(id=galery["id"]).exists():
            galerie = Galerie.objects.get(id=galery["id"])
            key = galery["key"]
            if key:
                if Galerie.objects.filter(place=key).exists():
                    extra = Galerie.objects.get(place=key)
                    extra.place = "nothing"
                    extra.save()
                galerie.place = key
                galerie.save()


def _assign_video_slots(videos):
    for video in videos:
        if VideoFile.objects.filter(id=video["id"]).exists():
            vid = VideoFile.objects.get(id=video["id"])
            key = video["key"]
            if key:
                if VideoFile.objects.filter(place=key).exists():
                    extra_vid = VideoFile.objects.get(place=key)
                    extra_vid.place = ""
                    extra_vid.save()
                vid.place = key
                vid.save()


def _save_text_values(name, values, lang):
    try:
        with transaction.atomic():
            text_content, created = TextContent.objects.get_or_create(name=name)

        for field in ["header", "title", "description", "buttonText"]:
            value = values.get(field, "")
            if created or value:
                setattr(text_content, f"{field}_{lang}", value)

        if lang == DEFAULT_LANGUAGE:
            for field in ["header", "title", "description", "buttonText"]:
                value = values.get(field, "")
                if created or value:
                    setattr(text_content, field, value)

        text_content.save()
    except IntegrityError:
        return JsonResponse({"error": f"Fehler: {name} existiert bereits"}, status=400)

    return None


@login_required(login_url="login")
def save_privacy_policy(request):
    if request.method != "POST":
        return JsonResponse({"error": "UngÃ¼ltige Anfrage"}, status=405)

    content_html = request.POST.get("content_html", "")
    owner_data = UserSettings.get_site_owner() or _get_user_settings(request.user)
    policy, _ = PrivacyPolicy.objects.get_or_create(pk=1)

    policy.use_html = True
    policy.content_html = PrivacyPolicy.prepare_content(content_html, owner_data, as_html=True)
    policy.save(update_fields=["use_html", "content_html", "updated_at"])

    return JsonResponse({"success": "DatenschutzerklÃ¤rung wurde gespeichert"}, status=200)

