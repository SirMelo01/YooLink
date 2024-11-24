from django.shortcuts import render, redirect, get_object_or_404
from yoolink.ycms.models import FAQ, Message, TeamMember, TextContent, fileentry, Galerie, OpeningHours, UserSettings, Product
import datetime
from django.http import HttpResponseRedirect


def get_opening_hours():
    opening_hours = {}
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    for day in days:
        if OpeningHours.objects.filter(day=day).exists():
            opening_hours[f"opening_{day.lower()}"] = OpeningHours.objects.get(day=day)
        else:
            opening_hours[f"opening_{day.lower()}"] = None
            
    user_settings = UserSettings.objects.filter(user__is_staff=False)
    if user_settings.exists():
        user_settings = user_settings.first()
        opening_hours["owner_data"] = user_settings
    return opening_hours

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

    # Galery
    if Galerie.objects.filter(place='main_hero').exists():
        context["heroImages"] = Galerie.objects.get(place='main_hero').images.all()
        
    if Galerie.objects.filter(place='main_responsive_desktop').exists():
        context['responsiveDesktopImages'] = Galerie.objects.get(place='main_responsive_desktop').images.all()
        
    if Galerie.objects.filter(place='main_responsive_handy').exists():
        context['responsiveHandyImages'] = Galerie.objects.get(place='main_responsive_handy').images.all()

    # Images
    if fileentry.objects.filter(place='main_cms').exists():
        context["cmsImage"] = fileentry.objects.get(place='main_cms')
    
    # Mitarbeiter
    active_team_members = TeamMember.objects.filter(active=True)
    context['teamMembers'] = active_team_members

    context.update(get_opening_hours())

    return render(request, 'pages/index.html', context=context)

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
