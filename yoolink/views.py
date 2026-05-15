from django.shortcuts import render, redirect, get_object_or_404
from yoolink.ycms.applications.content.models import Customer, PrivacyPolicy, TextContent
from yoolink.ycms.models import FAQ, Message, PricingCard, TeamMember, fileentry, Galerie, OpeningHours, UserSettings
import datetime
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import get_language_from_request, activate
from django.conf import settings

def get_opening_hours():
    opening_hours = {}
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    for day in days:
        if OpeningHours.objects.filter(day=day).exists():
            opening_hours[f"opening_{day.lower()}"] = OpeningHours.objects.get(day=day)
        else:
            opening_hours[f"opening_{day.lower()}"] = None
        
    # Muss überall sein
    if TextContent.objects.filter(name="footer").exists():
        opening_hours["footerText"] = TextContent.objects.get(name='footer')
        
    return opening_hours

def load_kunden(request):
    context = {}
    context.update(get_opening_hours())

    if TextContent.objects.filter(name="main_kunden").exists():
        context["kundenText"] = TextContent.objects.get(name='main_kunden')

    if TextContent.objects.filter(name="main_kunden2").exists():
        context["kundenText2"] = TextContent.objects.get(name='main_kunden2')

    customers_qs = list(
        Customer.objects.filter(active=True)
        .select_related("title_image", "logo")
        .order_by("order", "-published_date", "id")
    )
    references = [c for c in customers_qs if c.section == Customer.SECTION_REFERENCES]
    specials = [c for c in customers_qs if c.section == Customer.SECTION_SPECIAL]
    context["customers_references"] = references
    context["customers_special"] = specials
    context["customers_total"] = len(references) + len(specials)

    return render(request, 'pages/kunden.html', context=context)


def load_kunde_detail(request, slug):
    customer = (
        Customer.objects.filter(slug=slug, active=True, show_detail_page=True)
        .select_related("title_image", "banner_image", "logo", "gallery")
        .first()
    )
    if not customer:
        raise Http404("Kunde nicht gefunden")

    gallery_images = []
    if customer.gallery:
        gallery_images = list(customer.gallery.images.all())

    services = [line.strip() for line in (customer.services_text or "").splitlines() if line.strip()]

    related_customers = (
        Customer.objects.filter(active=True, show_detail_page=True)
        .exclude(pk=customer.pk)
        .order_by("-published_date", "order")[:3]
    )

    context = {
        "customer": customer,
        "gallery_images": gallery_images,
        "services": services,
        "related_customers": related_customers,
    }
    context.update(get_opening_hours())
    return render(request, "pages/kunde_detail.html", context=context)

def load_index(request):
    faq = FAQ.objects.all()

    context = {
        'FAQ': faq,
    }

    # Text Contents
    if TextContent.objects.filter(name="main_hero").exists():
        context["heroText"] = TextContent.objects.get(name='main_hero')

    if TextContent.objects.filter(name="main_responsive").exists():
        context["responsiveText"] = TextContent.objects.get(name='main_responsive')

    if TextContent.objects.filter(name="main_cms").exists():
        context["cmsText"] = TextContent.objects.get(name='main_cms')

    if TextContent.objects.filter(name="main_price").exists():
        context["priceText"] = TextContent.objects.get(name='main_price')

    if TextContent.objects.filter(name="main_team").exists():
        context["teamText"] = TextContent.objects.get(name='main_team')

    if TextContent.objects.filter(name="main_kunden").exists():
        context["kundenText"] = TextContent.objects.get(name='main_kunden')
    # Text Know-How
    if TextContent.objects.filter(name="main_know_how").exists():
        context["knowHowContent"] = TextContent.objects.get(name='main_know_how')
    # Know How contents
    if TextContent.objects.filter(name="main_know_how_card_1").exists():
        context["knowHowContentCard1"] = TextContent.objects.get(name='main_know_how_card_1')
    if TextContent.objects.filter(name="main_know_how_card_2").exists():
        context["knowHowContentCard2"] = TextContent.objects.get(name='main_know_how_card_2')
    if TextContent.objects.filter(name="main_know_how_card_3").exists():
        context["knowHowContentCard3"] = TextContent.objects.get(name='main_know_how_card_3')
    if TextContent.objects.filter(name="main_faq").exists():
        context["faqText"] = TextContent.objects.get(name='main_faq')
    # Galery
    if Galerie.objects.filter(place='main_hero').exists():
        context["heroImages"] = Galerie.objects.get(place='main_hero').images.all()
        
    if Galerie.objects.filter(place='main_responsive_desktop').exists():
        context['responsiveDesktopImages'] = Galerie.objects.get(place='main_responsive_desktop').images.all()
        
    if Galerie.objects.filter(place='main_responsive_handy').exists():
        context['responsiveHandyImages'] = Galerie.objects.get(place='main_responsive_handy').images.all()

    pricing_cards = PricingCard.objects.select_related("button").prefetch_related("features").filter(active=True)
    context["pricing_cards"] = pricing_cards

    # Images
    if fileentry.objects.filter(place='main_cms').exists():
        context["cmsImage"] = fileentry.objects.get(place='main_cms')
    
    # Mitarbeiter
    active_team_members = TeamMember.objects.filter(active=True)
    context['teamMembers'] = active_team_members

    context.update(get_opening_hours())

    return render(request, 'pages/index.html', context=context)


def load_logos(request):
    context = {}
    context.update(get_opening_hours())

    def get_text(name: str):
        return TextContent.objects.filter(name=name).first()

    def get_image(place: str):
        return fileentry.objects.filter(place=place).first()

    # Hero
    context["textContent_hero"] = get_text("main_logos_hero")
    context["textContent_hero_secondary"] = get_text("main_logos_hero_secondary")
    context["image_hero_logo_1"] = get_image("main_logos_hero_logo_1")
    context["image_hero_logo_2"] = get_image("main_logos_hero_logo_2")
    context["image_hero_logo_3"] = get_image("main_logos_hero_logo_3")
    context["image_hero_logo_4"] = get_image("main_logos_hero_logo_4")
    context["image_hero_logo_5"] = get_image("main_logos_hero_logo_5")

    # Warum
    context["textContent_warum"] = get_text("main_logos_warum")
    context["textContent_warum_card1"] = get_text("main_logos_warum_card1")
    context["textContent_warum_card2"] = get_text("main_logos_warum_card2")
    context["textContent_warum_card3"] = get_text("main_logos_warum_card3")

    # Leistungsbereiche
    context["textContent_leistungen"] = get_text("main_logos_leistungen")
    context["textContent_leistungen_card1"] = get_text("main_logos_leistungen_card1")
    context["textContent_leistungen_card1_bullet1"] = get_text("main_logos_leistungen_card1_bullet1")
    context["textContent_leistungen_card1_bullet2"] = get_text("main_logos_leistungen_card1_bullet2")
    context["textContent_leistungen_card1_bullet3"] = get_text("main_logos_leistungen_card1_bullet3")
    context["textContent_leistungen_card2"] = get_text("main_logos_leistungen_card2")
    context["textContent_leistungen_card2_bullet1"] = get_text("main_logos_leistungen_card2_bullet1")
    context["textContent_leistungen_card2_bullet2"] = get_text("main_logos_leistungen_card2_bullet2")
    context["textContent_leistungen_card2_bullet3"] = get_text("main_logos_leistungen_card2_bullet3")
    context["textContent_leistungen_card3"] = get_text("main_logos_leistungen_card3")
    context["textContent_leistungen_card3_bullet1"] = get_text("main_logos_leistungen_card3_bullet1")
    context["textContent_leistungen_card3_bullet2"] = get_text("main_logos_leistungen_card3_bullet2")
    context["textContent_leistungen_card3_bullet3"] = get_text("main_logos_leistungen_card3_bullet3")
    context["textContent_leistungen_premium"] = get_text("main_logos_leistungen_premium")
    context["textContent_leistungen_premium_bullet1"] = get_text("main_logos_leistungen_premium_bullet1")
    context["textContent_leistungen_premium_bullet2"] = get_text("main_logos_leistungen_premium_bullet2")
    context["textContent_leistungen_premium_bullet3"] = get_text("main_logos_leistungen_premium_bullet3")
    context["textContent_leistungen_premium_bullet4"] = get_text("main_logos_leistungen_premium_bullet4")

    # Premium Showcase (Goldener Schnitt)
    context["textContent_premium"] = get_text("main_logos_premium")
    context["textContent_premium_bullet1"] = get_text("main_logos_premium_bullet1")
    context["textContent_premium_bullet2"] = get_text("main_logos_premium_bullet2")
    context["textContent_premium_bullet3"] = get_text("main_logos_premium_bullet3")

    # Designprozess
    context["textContent_prozess"] = get_text("main_logos_prozess")
    context["textContent_prozess_step1"] = get_text("main_logos_prozess_step1")
    context["textContent_prozess_step2"] = get_text("main_logos_prozess_step2")
    context["textContent_prozess_step3"] = get_text("main_logos_prozess_step3")
    context["textContent_prozess_step4"] = get_text("main_logos_prozess_step4")
    context["textContent_prozess_step5"] = get_text("main_logos_prozess_step5")

    # Lieferumfang
    context["textContent_lieferumfang"] = get_text("main_logos_lieferumfang")
    context["textContent_lieferumfang_bullet1"] = get_text("main_logos_lieferumfang_bullet1")
    context["textContent_lieferumfang_bullet2"] = get_text("main_logos_lieferumfang_bullet2")
    context["textContent_lieferumfang_bullet3"] = get_text("main_logos_lieferumfang_bullet3")
    context["textContent_lieferumfang_bullet4"] = get_text("main_logos_lieferumfang_bullet4")
    context["textContent_lieferumfang_bullet5"] = get_text("main_logos_lieferumfang_bullet5")

    # USP
    context["textContent_usp"] = get_text("main_logos_usp")
    context["textContent_usp_card1"] = get_text("main_logos_usp_card1")
    context["textContent_usp_card2"] = get_text("main_logos_usp_card2")
    context["textContent_usp_card3"] = get_text("main_logos_usp_card3")

    # Bottom CTA
    context["textContent_bottomcta"] = get_text("main_logos_bottomcta")

    return render(request, 'pages/leistungen_logos.html', context=context)


def load_medien(request):
    context = {}
    context.update(get_opening_hours())
    return render(request, 'pages/leistungen_medien.html', context=context)


def load_webdesign(request):
    context = {}
    context.update(get_opening_hours())

    def get_text(name: str):
        return TextContent.objects.filter(name=name).first()

    # Hero
    context["textContent_hero"] = get_text("main_webdesign_hero")
    context["textContent_hero_secondary"] = get_text("main_webdesign_hero_secondary")
    context["textContent_hero_badge1"] = get_text("main_webdesign_hero_badge1")
    context["textContent_hero_badge2"] = get_text("main_webdesign_hero_badge2")
    context["textContent_hero_badge3"] = get_text("main_webdesign_hero_badge3")

    # Ansatz
    context["textContent_ansatz"] = get_text("main_webdesign_ansatz")
    context["textContent_ansatz_card1"] = get_text("main_webdesign_ansatz_card1")
    context["textContent_ansatz_card2"] = get_text("main_webdesign_ansatz_card2")
    context["textContent_ansatz_card3"] = get_text("main_webdesign_ansatz_card3")

    # Prozess
    context["textContent_prozess"] = get_text("main_webdesign_prozess")
    context["textContent_prozess_step1"] = get_text("main_webdesign_prozess_step1")
    context["textContent_prozess_step2"] = get_text("main_webdesign_prozess_step2")
    context["textContent_prozess_step3"] = get_text("main_webdesign_prozess_step3")
    context["textContent_prozess_step4"] = get_text("main_webdesign_prozess_step4")
    context["textContent_prozess_step5"] = get_text("main_webdesign_prozess_step5")

    # Tech Stack
    context["textContent_tech"] = get_text("main_webdesign_tech")
    context["textContent_tech_bullet1"] = get_text("main_webdesign_tech_bullet1")
    context["textContent_tech_bullet2"] = get_text("main_webdesign_tech_bullet2")
    context["textContent_tech_bullet3"] = get_text("main_webdesign_tech_bullet3")
    context["textContent_tech_bullet4"] = get_text("main_webdesign_tech_bullet4")

    # Hosting bei Hetzner
    context["textContent_hosting"] = get_text("main_webdesign_hosting")
    context["textContent_hosting_tile1"] = get_text("main_webdesign_hosting_tile1")
    context["textContent_hosting_tile2"] = get_text("main_webdesign_hosting_tile2")
    context["textContent_hosting_tile3"] = get_text("main_webdesign_hosting_tile3")
    context["textContent_hosting_tile4"] = get_text("main_webdesign_hosting_tile4")
    context["textContent_hosting_bullet1"] = get_text("main_webdesign_hosting_bullet1")
    context["textContent_hosting_bullet2"] = get_text("main_webdesign_hosting_bullet2")
    context["textContent_hosting_bullet3"] = get_text("main_webdesign_hosting_bullet3")
    context["textContent_hosting_bullet4"] = get_text("main_webdesign_hosting_bullet4")
    context["textContent_hosting_bullet5"] = get_text("main_webdesign_hosting_bullet5")

    # Technische Schwerpunkte
    context["textContent_schwerpunkte"] = get_text("main_webdesign_schwerpunkte")
    context["textContent_schwerpunkte_card1"] = get_text("main_webdesign_schwerpunkte_card1")
    context["textContent_schwerpunkte_card1_bullet1"] = get_text("main_webdesign_schwerpunkte_card1_bullet1")
    context["textContent_schwerpunkte_card1_bullet2"] = get_text("main_webdesign_schwerpunkte_card1_bullet2")
    context["textContent_schwerpunkte_card1_bullet3"] = get_text("main_webdesign_schwerpunkte_card1_bullet3")
    context["textContent_schwerpunkte_card2"] = get_text("main_webdesign_schwerpunkte_card2")
    context["textContent_schwerpunkte_card2_bullet1"] = get_text("main_webdesign_schwerpunkte_card2_bullet1")
    context["textContent_schwerpunkte_card2_bullet2"] = get_text("main_webdesign_schwerpunkte_card2_bullet2")
    context["textContent_schwerpunkte_card2_bullet3"] = get_text("main_webdesign_schwerpunkte_card2_bullet3")
    context["textContent_schwerpunkte_card3"] = get_text("main_webdesign_schwerpunkte_card3")
    context["textContent_schwerpunkte_card3_bullet1"] = get_text("main_webdesign_schwerpunkte_card3_bullet1")
    context["textContent_schwerpunkte_card3_bullet2"] = get_text("main_webdesign_schwerpunkte_card3_bullet2")
    context["textContent_schwerpunkte_card3_bullet3"] = get_text("main_webdesign_schwerpunkte_card3_bullet3")
    context["textContent_schwerpunkte_card4"] = get_text("main_webdesign_schwerpunkte_card4")
    context["textContent_schwerpunkte_card4_bullet1"] = get_text("main_webdesign_schwerpunkte_card4_bullet1")
    context["textContent_schwerpunkte_card4_bullet2"] = get_text("main_webdesign_schwerpunkte_card4_bullet2")
    context["textContent_schwerpunkte_card4_bullet3"] = get_text("main_webdesign_schwerpunkte_card4_bullet3")

    # Warum dieser Ansatz
    context["textContent_warum"] = get_text("main_webdesign_warum")
    context["textContent_warum_card1"] = get_text("main_webdesign_warum_card1")
    context["textContent_warum_card2"] = get_text("main_webdesign_warum_card2")
    context["textContent_warum_card3"] = get_text("main_webdesign_warum_card3")
    context["textContent_warum_card4"] = get_text("main_webdesign_warum_card4")

    # Bottom CTA
    context["textContent_bottomcta"] = get_text("main_webdesign_bottomcta")

    return render(request, 'pages/leistungen_webdesign.html', context=context)


def load_visitenkarte(request):
    context = {}
    context.update(get_opening_hours())

    def get_text(name: str):
        return TextContent.objects.filter(name=name).first()

    def get_image(place: str):
        return fileentry.objects.filter(place=place).first()

    # Hero
    context["textContent_hero"] = get_text("main_visitenkarte_hero")
    context["textContent_hero_secondary"] = get_text("main_visitenkarte_hero_secondary")
    context["image_hero_front"] = get_image("main_visitenkarte_hero_front")
    context["image_hero_back"] = get_image("main_visitenkarte_hero_back")

    # Showcase / Bisherige Arbeiten
    context["textContent_showcase"] = get_text("main_visitenkarte_showcase")
    context["textContent_showcase_label_front"] = get_text("main_visitenkarte_showcase_label_front")
    context["textContent_showcase_label_back"] = get_text("main_visitenkarte_showcase_label_back")
    context["image_showcase_front"] = get_image("main_visitenkarte_showcase_front")
    context["image_showcase_back"] = get_image("main_visitenkarte_showcase_back")

    # Formate
    context["textContent_formate"] = get_text("main_visitenkarte_formate")
    context["textContent_format_standard"] = get_text("main_visitenkarte_format_standard")
    context["textContent_format_slim"] = get_text("main_visitenkarte_format_slim")

    # Papier / Qualität
    context["textContent_papier"] = get_text("main_visitenkarte_papier")
    context["textContent_papier_card1"] = get_text("main_visitenkarte_papier_card1")
    context["textContent_papier_card2"] = get_text("main_visitenkarte_papier_card2")
    context["textContent_papier_card3"] = get_text("main_visitenkarte_papier_card3")

    # Bottom CTA
    context["textContent_bottomcta"] = get_text("main_visitenkarte_bottomcta")

    return render(request, 'pages/leistungen_visitenkarte.html', context=context)


def load_cmsinfo(request):
    context = {}

    def get_text(name: str):
        return TextContent.objects.filter(name=name).first()

    def get_image(place: str):
        return fileentry.objects.filter(place=place).first()

    context["textContent_hero"] = TextContent.objects.filter(name="main_cmsinfo_hero").first()
    context["textContent_sec1"] = get_text("main_cmsinfo_sec1")
    context["textContent_sec2"] = get_text("main_cmsinfo_sec2")
    context["textContent_blog"] = get_text("main_cmsinfo_blog")
    context["textContent_blog_bullet1"] = get_text("main_cmsinfo_blog_bullet1")
    context["textContent_blog_bullet2"] = get_text("main_cmsinfo_blog_bullet2")
    context["textContent_blog_bullet3"] = get_text("main_cmsinfo_blog_bullet3")

    context["textContent_company"] = get_text("main_cmsinfo_company")
    context["textContent_trust"] = get_text("main_cmsinfo_trust")

    context["textContent_stat1"] = get_text("main_cmsinfo_stat1")
    context["textContent_stat2"] = get_text("main_cmsinfo_stat2")
    context["textContent_stat3"] = get_text("main_cmsinfo_stat3")
    context["textContent_stat4"] = get_text("main_cmsinfo_stat4")

    context["textContent_bottomcta"] = get_text("main_cmsinfo_bottomcta")

    context["textContent_company_bullet1"] = get_text("main_cmsinfo_company_bullet1")
    context["textContent_company_bullet2"] = get_text("main_cmsinfo_company_bullet2")
    context["textContent_company_bullet3"] = get_text("main_cmsinfo_company_bullet3")
    context["textContent_company_bullet4"] = get_text("main_cmsinfo_company_bullet4")

    context["image_sec1_card_1"] = get_image("main_cmsinfo_sec1_card_1")
    context["image_sec1_card_2"] = get_image("main_cmsinfo_sec1_card_2")
    context["image_sec1_card_3"] = get_image("main_cmsinfo_sec1_card_3")
    context["image_sec1_card_4"] = get_image("main_cmsinfo_sec1_card_4")
    context["image_sec1_preview_1"] = get_image("main_cmsinfo_sec1_preview_1")
    context["image_sec1_preview_2"] = get_image("main_cmsinfo_sec1_preview_2")
    context["image_sec1_preview_3"] = get_image("main_cmsinfo_sec1_preview_3")
    context["image_sec1_preview_4"] = get_image("main_cmsinfo_sec1_preview_4")
    context["image_sec2_card_1"] = get_image("main_cmsinfo_sec2_card_1")
    context["image_sec2_card_2"] = get_image("main_cmsinfo_sec2_card_2")
    context["image_sec2_card_3"] = get_image("main_cmsinfo_sec2_card_3")
    context["image_sec2_preview_1"] = get_image("main_cmsinfo_sec2_preview_1")
    context["image_sec2_preview_2"] = get_image("main_cmsinfo_sec2_preview_2")
    context["image_sec2_preview_3"] = get_image("main_cmsinfo_sec2_preview_3")
    context["image_blog"] = get_image("main_cmsinfo_blog_image")
    context["image_company"] = get_image("main_cmsinfo_company_image")

    return render(request, 'pages/cmsinfo.html', context=context)


def leistungen_view(request):
    context = {}
    context.update(get_opening_hours())
    logo_slot_keys = [
        "main_leistungen_logo_1",
        "main_leistungen_logo_2",
        "main_leistungen_logo_3",
        "main_leistungen_logo_4",
    ]

    def get_text(name: str):
        return TextContent.objects.filter(name=name).first()

    def get_image(place: str):
        return fileentry.objects.filter(place=place).first()

    legacy_logo_image = get_image("main_leistungen_logos_image")

    context["textContent_intro"] = get_text("main_leistungen_intro")
    context["textContent_cms"] = get_text("main_leistungen_cms")
    context["textContent_webdesign"] = get_text("main_leistungen_webdesign")
    context["textContent_logos"] = get_text("main_leistungen_logos")
    context["textContent_custom"] = get_text("main_leistungen_custom")

    context["image_cms"] = get_image("main_leistungen_cms_image")
    context["image_webdesign"] = get_image("main_leistungen_webdesign_image")
    context["image_logo_1"] = get_image(logo_slot_keys[0]) or legacy_logo_image
    context["image_logo_2"] = get_image(logo_slot_keys[1])
    context["image_logo_3"] = get_image(logo_slot_keys[2])
    context["image_logo_4"] = get_image(logo_slot_keys[3])
    context["image_custom"] = get_image("main_leistungen_custom_image")

    context["textContent_visitenkarten"] = get_text("main_leistungen_visitenkarten")
    context["image_vk_1"] = get_image("main_leistungen_vk_1")
    context["image_vk_2"] = get_image("main_leistungen_vk_2")
    context["image_vk_3"] = get_image("main_leistungen_vk_3")
    context["image_vk_4"] = get_image("main_leistungen_vk_4")

    context["textContent_medien"] = get_text("main_leistungen_medien")
    context["image_medien"] = get_image("main_leistungen_medien_image")

    return render(request, 'pages/leistungen.html', context=context)


def datenschutz_view(request):
    owner_data = UserSettings.get_site_owner()
    policy = PrivacyPolicy.objects.first()
    privacy_content_html = ""
    use_policy = policy is not None

    if policy:
        if policy.use_html and policy.content_html.strip():
            privacy_content_html = policy.render_content(owner_data)
        elif policy.content_text.strip():
            privacy_content_html = policy.render_content(owner_data)

    return render(
        request,
        'pages/datenschutz.html',
        {
            'privacy_content_html': privacy_content_html,
            'use_policy': use_policy,
            'owner_data': owner_data,
        },
    )



from .forms import ContactForm
def kontaktform(request):
    success = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Hier Nachricht verarbeiten und speichern
            Message.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                title=form.cleaned_data['title'],
                message=form.cleaned_data['message'],
            )
            return render(request, 'pages/kontakt.html', {'success': True})
    else:
        form = ContactForm()

    owner_data = UserSettings.get_site_owner()
    return render(
        request,
        'pages/kontakt.html',
        {
            'form': form,
            'success': success,
            'recaptcha_public_key': settings.RECAPTCHA_PUBLIC_KEY,
            'google_maps_embed_api_key': settings.GOOGLE_MAPS_EMBED_API_KEY,
            'owner_data': owner_data,
        },
    )

# Authentication

