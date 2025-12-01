from django.shortcuts import render, redirect, get_object_or_404
from yoolink.ycms.models import FAQ, Message, PricingCard, TeamMember, TextContent, fileentry, Galerie, OpeningHours, UserSettings, Product
import datetime
from django.http import HttpResponseRedirect
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

    return render(request, 'pages/kunden.html', context=context)

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



def load_cmsinfo(request):

    context = {
    }

    return render(request, 'pages/cmsinfo.html', context=context)






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

    return render(request, 'pages/kontakt.html', {'form': form, 'success': success})

def skills_view(request):
    context = {}
    context.update(get_opening_hours())  # falls Öffnungszeiten unten benötigt werden

    # Texte holen
    context["textContent_intro"] = TextContent.objects.filter(name="main_skills_intro").first()
    context["textContent_cms"] = TextContent.objects.filter(name="main_skills_cms").first()
    context["textContent_webdesign"] = TextContent.objects.filter(name="main_skills_webdesign").first()
    context["textContent_logos"] = TextContent.objects.filter(name="main_skills_logos").first()
    context["textContent_custom"] = TextContent.objects.filter(name="main_skills_custom").first()

    return render(request, 'pages/skills.html', context)

def shop(request):
   context={"products": Product.objects.filter(is_active=True)}
   context.update(get_opening_hours())
   return render(request, 'pages/shop.html', context)

def detail(request, product_id, slug):
    product = get_object_or_404(Product, id=product_id, slug=slug)
    last_url = request.META.get('HTTP_REFERER')
    if not product.is_active:
        return render(request, "pages/errors/error.html", {
            "error": "Dieses Produkt ist nicht mehr verfügbar",
            "saveLink": last_url if last_url else '/'
        })
    context={"product": product}
    context.update(get_opening_hours())
    return render(request, 'pages/detail.html', context)
