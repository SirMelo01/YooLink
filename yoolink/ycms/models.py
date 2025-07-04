from django.db import models

# Create your models here.

from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save
from yoolink.users.models import User
from django.utils.text import slugify
from django.utils import timezone
import uuid
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ValidationError

## Produktiv und funktioniert

class FAQ(models.Model):
    question = models.CharField(max_length=255, default="")
    answer = models.TextField(default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.id:
            max_order = FAQ.objects.aggregate(models.Max('order'))['order__max']
            self.order = 1 if max_order is None else max_order + 1
        super(FAQ, self).save(*args, **kwargs)

    def __str__(self):
        return self.question

## Produktiv und funktioniert
def unique_image_name(instance, filename):
    """
    Generate a unique filename by appending a timestamp.
    """
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    base, ext = os.path.splitext(filename)
    return f"yoolink/images/{slugify(base)}_{timestamp}{ext}"

class fileentry(models.Model):
    file = models.ImageField(upload_to=unique_image_name)
    uploaddate = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default="Bildtitel")
    place = models.CharField(max_length=60, default="")

    def __str__(self):
        return os.path.basename(self.file.name)
    
    def delete(self, *args, **kwargs):
        self.file.storage.delete(self.file.name)
        super(fileentry, self).delete(*args, **kwargs)

    def delete_model_only(self, *args, **kwargs):
        super(fileentry, self).delete(*args, **kwargs) 

def unique_anyfile_name(instance, filename):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    base, ext = os.path.splitext(filename)
    return f"yoolink/uploads/{slugify(base)}_{timestamp}{ext}"

def validate_file_extension(value):
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webm',
                          '.pdf', '.zip', '.docx', '.xlsx', '.txt']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'Dateiformat "{ext}" wird nicht unterstützt.')

class AnyFile(models.Model):
    file = models.FileField(upload_to=unique_anyfile_name, validators=[validate_file_extension])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default="", blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        self.file.storage.delete(self.file.name)
        super(AnyFile, self).delete(*args, **kwargs)

def unique_video_name(instance, filename):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    base, ext = os.path.splitext(filename)
    return f"yoolink/videos/{slugify(base)}_{timestamp}{ext}"

def validate_video_extension(value):
    allowed = ['.mp4', '.mov', '.webm']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed:
        raise ValidationError(f'Dateiformat "{ext}" wird nicht unterstützt.')

def validate_image_extension(value):
    allowed = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed:
        raise ValidationError(f'Bildformat "{ext}" wird nicht unterstützt.')

def validate_vtt_extension(value):
    if not value.name.lower().endswith('.vtt'):
        raise ValidationError('Nur .vtt Untertiteldateien sind erlaubt.')

class VideoFile(models.Model):
    file = models.FileField(
        upload_to=unique_video_name,
        validators=[validate_video_extension],
        help_text="Video-Datei (.mp4, .mov, .webm)"
    )
    thumbnail = models.ImageField(
        upload_to="yoolink/thumbnails/",
        validators=[validate_image_extension],
        blank=True,
        null=True,
        help_text="Poster-Thumbnail für Video"
    )
    subtitle_file = models.FileField(
        upload_to="yoolink/subtitles/",
        validators=[validate_vtt_extension],
        blank=True,
        null=True,
        help_text="Optional: Untertitel im .vtt Format"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, help_text="Titel für das Video", blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(help_text="Beschreibung / Caption des Videos", blank=True)
    duration = models.DurationField(
        blank=True,
        null=True,
        help_text="Laufzeit des Videos (z.B. für SEO oder schema.org)"
    )
    alt_text = models.CharField(max_length=255, help_text="Alt-Text für SEO & Barrierefreiheit", blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Kommaseparierte Tags (optional)")
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while VideoFile.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.storage.delete(self.file.name)
        if self.thumbnail:
            self.thumbnail.storage.delete(self.thumbnail.name)
        if self.subtitle_file:
            self.subtitle_file.storage.delete(self.subtitle_file.name)
        super().delete(*args, **kwargs)


def upload_to_galery_image(instance, filename):
    """
    Generate a unique filename by appending a timestamp.
    """
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    base, ext = os.path.splitext(filename)
    return f"yoolink/galeryImages/{slugify(base)}_{timestamp}{ext}"

class GaleryImage(models.Model):
    upload = models.ImageField(upload_to=upload_to_galery_image)
    uploaddate = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default="Bildtitel")

    def __str__(self):
        return str(self.pk)
    
    def delete(self, *args, **kwargs):
        self.upload.storage.delete(self.upload.name)
        super(GaleryImage, self).delete(*args, **kwargs)

    def delete_model_only(self, *args, **kwargs):
        super(GaleryImage, self).delete(*args, **kwargs)

class Galerie(models.Model):
    title = models.CharField(max_length=100, default="Titel")
    description = models.TextField(default="")
    active = models.BooleanField(default=True)
    place = models.CharField(max_length=60, default="")
    images = models.ManyToManyField(GaleryImage)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

"""
Blog
"""

def upload_to_blog_image(instance, filename):
    return f"yoolink/blogs/{instance.id}/{filename}"
def default_code():
    return dict()
class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, default='default-slug', max_length=255)
    title_image = models.ImageField(upload_to=upload_to_blog_image, default="", blank=True)
    date = models.DateField(auto_now_add=True)  # Automatically set on creation
    last_updated = models.DateField(auto_now=True)  # Automatically updated on save
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(default="This Blog is empty")
    code = models.JSONField(default=default_code)
    active = models.BooleanField(default=False)
    description = models.TextField(default="")

    def delete(self, *args, **kwargs):
        self.title_image.storage.delete(self.title_image.name)
        super(Blog, self).delete(*args, **kwargs)
    
    def __str__(self):
        return self.title + ' | ' + str(self.author)
    
    def save(self, *args, **kwargs):
        # Slugify the title and store it in the slug field
        self.slug = slugify(self.title)

        # Call the parent class's save method to actually save the model
        super(Blog, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:blog-detail", kwargs={"pk": self.pk, "slug_title": self.slug})
    
    

""" 
Products
"""
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=200) 
    slug = models.SlugField(unique=True, max_length=255)
    
    def save(self, *args, **kwargs):
        # Slugify the title and store it in the slug field
        self.slug = slugify(self.name)

        # Call the parent class's save method to actually save the model
        super(Brand, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

def upload_to_product_image(instance, filename):
    return f"yoolink/products/{instance.id}/{filename}"

class Product(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    title_image = models.ImageField(upload_to=upload_to_product_image, default="", blank=True)
    gallery = models.ForeignKey(Galerie, on_delete=models.SET_NULL, blank=True, null=True)
    is_reduced = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, default=0)
    online_sell = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Slugify the title and store it in the slug field
        self.slug = slugify(self.title)

        # Call the parent class's save method to actually save the model
        super(Product, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product-detail", kwargs={"product_id": self.pk, "slug": self.slug})

class ShippingAddress(models.Model):
    prename = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    # state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.prename} {self.name}'s Shipping Address"
    
    def get_shipping_address(self):
        return f"{self.address}, {self.postal_code} {self.city}, {self.country}"
    
    def get_buyer_name(self):
        return f"{self.prename} {self.name}"
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Offen'),
        ('PAID', 'Bezahlt'),
        ('READY_FOR_PICKUP', 'Bereit zur Abholung'),
        ('SHIPPED', 'Versendet'),
        ('COMPLETED', 'Abgeschlossen'),
    ]
    SHIPPING_CHOICES = [
        ('SHIPPING', 'Lieferung'),
        ('PICKUP', 'Abholung'),
    ]
    PAYMENT_CHOICES = [
        ('TRANSFER', 'Überweisung/Paypal'),
        ('CASH', 'Barzahlung'),
    ]

    buyer_email = models.EmailField()
    buyer_address = models.ForeignKey(ShippingAddress, null=True, on_delete=models.DO_NOTHING)
    verified = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    payment = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    shipping = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='SHIPPING')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]
    
    def get_payment_display(self):
        return dict(self.PAYMENT_CHOICES)[self.payment]
    
    def get_shipping_display(self):
        return dict(self.SHIPPING_CHOICES)[self.shipping]

    def total(self):
        return sum(item.subtotal() for item in self.orderitem_set.all()) + self.shipping_price()  # Adjusted to use the related name orderitem_set

    def total_without_shipping(self):
        return sum(item.subtotal() for item in self.orderitem_set.all())  # Adjusted to use the related name orderitem_set

    def total_with_tax(self):
        return self.total() - self.calculate_tax()

    def calculate_tax(self):
        return self.total() * Decimal('0.19')
    
    def shipping_price(self):
        total_weight_kg = self.total_weight_kg()
        
        if self.shipping and self.shipping == 'PICKUP':
            return Decimal('0.0')

        if total_weight_kg <= Decimal('2'):
            return Decimal('5.49')
        elif total_weight_kg <= Decimal('5'):
            return Decimal('6.99')
        elif total_weight_kg <= Decimal('10'):
            return Decimal('10.49')
        elif total_weight_kg <= Decimal('31.5'):
            return Decimal('19.99')
        elif total_weight_kg <= Decimal('50.5'):
            return Decimal('19.99')
        else:
            # Handle weights above 31.5 kg
            return Decimal('19.99')  # You may want to handle this case differently based on your business logic

    
    def total_weight_kg(self):
        total_weight = Decimal('0')
        for item in self.orderitem_set.all():
            total_weight += item.product_weight()
        return total_weight

    def total_discount(self):
        total_discount = 0
        for item in self.orderitem_set.filter(is_discounted=True):
            if item.discounted_price is not None:
                total_discount += (item.unit_price - item.discounted_price) * item.quantity
        return total_discount

    def __str__(self):
        return f"Order #{self.pk} - {self.buyer_email} - {self.status}"

    def total_quantity(self):
        return sum(item.quantity for item in self.orderitem_set.all())  # Adjusted to use the related name orderitem_set

    def delete(self, *args, **kwargs):
        # Check if the ShippingAddress is only associated with this Order
        # Überprüfen, ob andere Bestellungen dieselbe Versandadresse verwenden
        other_orders_with_same_address = Order.objects.filter(buyer_address=self.buyer_address).exclude(pk=self.pk)
        
        if other_orders_with_same_address.exists():
            # Wenn andere Bestellungen dieselbe Versandadresse verwenden, löschen Sie diese nicht
            super().delete(*args, **kwargs)
        else:
            # Wenn keine anderen Bestellungen dieselbe Versandadresse verwenden, löschen Sie sie
            self.buyer_address.delete()
            super().delete(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, default=1)  # ForeignKey to Order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_discounted = models.BooleanField(default=False)  # Flag to indicate if it's a discounted item
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def get_price(self):
        if self.is_discounted and self.discounted_price:
            return self.discounted_price
        return self.unit_price

    def subtotal(self):
        return self.quantity * self.get_price()
    
    def product_weight(self):
        # Return the weight of the product multiplied by the quantity
        return self.product.weight * self.quantity if self.product.weight else 0

    def __str__(self):
        return f"{self.product.title} - {self.quantity} units - {'Discounted' if self.is_discounted else 'Normal'}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=255)
    email = models.EmailField()
    comment = models.TextField(default='')
    rating = models.PositiveIntegerField(default=5)  # Assuming a rating out of 5

    def __str__(self):
        return f"{self.user_name} - {self.product.title} - {self.rating} stars"


"""
Messages
"""

class Message(models.Model):
    name = models.CharField(max_length=70)
    title = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=60)
    message = models.CharField(max_length=3000)
    date = models.DateField(auto_now_add=True, null=True)
    seen = models.BooleanField(default=False)

class TextContent(models.Model):
    name = models.CharField(max_length=50, default="", unique=True)
    header = models.CharField(max_length=100, default="")
    title = models.CharField(max_length=140, default="")
    description = models.TextField(default="")
    buttonText = models.CharField(max_length=120, default="")

def upload_to_user_settings(instance, filename):
    return f"yoolink/settings/{instance.id}/{filename}"
class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, default='')
    full_name = models.CharField(max_length=255, default='')
    company_name = models.CharField(max_length=255, default='')
    tel_number = models.CharField(max_length=18, default='')
    fax_number = models.CharField(max_length=18, default='')
    mobile_number = models.CharField(max_length=18, default='')
    website = models.URLField(blank=True, default='')
    address = models.CharField(max_length=255, default='')
    vacation = models.BooleanField(default=False)
    vacationText = models.CharField(max_length=200, default='Wir sind aktuell im Urlaub. Ab dem XX.XX sind wir wieder für Sie da!')
    global_font = models.CharField(max_length=60, default='font-sans')
    logo = models.ImageField(upload_to=upload_to_user_settings, default="", blank=True)
    favicon = models.ImageField(upload_to=upload_to_user_settings, default="", blank=True)

    def __str__(self):
        return f"{self.full_name}'s Einstellungen"

class OpeningHours(models.Model):
    DAY_CHOICES = [
        ('MON', 'Montag'),
        ('TUE', 'Dienstag'),
        ('WED', 'Mittwoch'),
        ('THU', 'Donnerstag'),
        ('FRI', 'Freitag'),
        ('SAT', 'Samstag'),
        ('SUN', 'Sonntag'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opening_hours')
    day = models.CharField(max_length=3, choices=DAY_CHOICES, unique=True)
    is_open = models.BooleanField(default=False)
    start_time = models.TimeField(default='08:00')  # Set default start time to 8 o'clock
    end_time = models.TimeField(default='14:00')    # Set default end time to 14 o'clock
    has_lunch_break = models.BooleanField(default=False)
    lunch_break_start = models.TimeField(blank=True, null=True)
    lunch_break_end = models.TimeField(blank=True, null=True)
    
    def calculate_opening_periods(self):
        """
        Berechnet die Öffnungszeiten mit Berücksichtigung der Mittagspause.
        Gibt eine Liste von Zeiträumen zurück, z. B. [(08:00, 12:00), (13:00, 18:00)].
        """
        if self.is_open:
            if self.has_lunch_break and self.lunch_break_start and self.lunch_break_end:
                return [
                    (self.start_time, self.lunch_break_start),
                    (self.lunch_break_end, self.end_time),
                ]
            return [(self.start_time, self.end_time)]
        return []

    def get_day(self):
        return dict(self.DAY_CHOICES)[self.day]

    def __str__(self):
        return f"Opening hours for {self.user.username} on {self.get_day_display()}"
    
class TeamMember(models.Model):
    full_name = models.CharField(max_length=120, default='')
    active = models.BooleanField(default=True)
    image = models.CharField(max_length=200, default='')
    age = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True)
    years_with_team = models.PositiveIntegerField(default=0)
    position = models.CharField(max_length=100, default="Mitarbeiter")
    note = models.TextField(default="")

    def __str__(self):
        return self.full_name
    
from django.db import models


class PricingCard(models.Model):
    title = models.CharField(max_length=100, verbose_name="Titel")
    monthly_price = models.CharField(max_length=20, verbose_name="Monatlicher Preis", help_text="z.B. '25 €' oder '? €'")
    one_time_price = models.CharField(max_length=50, verbose_name="Einmalzahlung", help_text="z.B. '250 €' oder '? €'")
    description = models.TextField(verbose_name="Beschreibung", blank=True, help_text="Kleiner Infotext unter dem Button")
    order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge", help_text="Reihenfolge der Karte auf der Seite")
    animation = models.CharField(
        max_length=50,
        choices=[
            ('fade-right', 'Fade Right'),
            ('fade-left', 'Fade Left'),
            ('zoom-in', 'Zoom In'),
            ('fade-up', 'Fade Up'),
        ],
        default='fade-up',
        verbose_name="AOS-Animation"
    )
    animation_delay = models.PositiveIntegerField(default=100, verbose_name="Animationsverzögerung (ms)")
    button = models.ForeignKey(
        'Button',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Zugehöriger Button"
    )
    active = models.BooleanField(default=True, verbose_name="Aktiv")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        verbose_name = "Pricing-Karte"
        verbose_name_plural = "Pricing-Karten"


class PricingFeature(models.Model):
    pricing_card = models.ForeignKey(PricingCard, related_name='features', on_delete=models.CASCADE)
    text = models.CharField(max_length=200, verbose_name="Featuretext")
    order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")

    def __str__(self):
        return f"{self.pricing_card.title}: {self.text}"

    class Meta:
        ordering = ['order']
        verbose_name = "Feature"
        verbose_name_plural = "Features"

class Button(models.Model):
    text = models.CharField(max_length=100, verbose_name="Button-Text")
    url = models.URLField(max_length=500, verbose_name="Ziel-URL")
    hover_text = models.CharField(
        max_length=200,
        verbose_name="Tooltip (Hover-Text)",
        blank=True,
        help_text="Optionaler Text, der beim Hover angezeigt wird"
    )
    target = models.CharField(
        max_length=20,
        choices=[
            ("_self", "Gleiches Fenster (_self)"),
            ("_blank", "Neuer Tab (_blank)"),
            ("_parent", "Elternelement (_parent)"),
            ("_top", "Oberstes Fenster (_top)"),
        ],
        default="_self",
        verbose_name="Link-Ziel (_blank etc.)"
    )
    css_classes = models.CharField(
        max_length=300,
        verbose_name="CSS-Klassen",
        blank=True,
        help_text="Optional: Zusätzliche Tailwind oder CSS-Klassen"
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Icon (optional)",
        help_text="z.B. Heroicon oder FontAwesome Klassenname"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")

    def __str__(self):
        return f"{self.text} → {self.url}"

    class Meta:
        ordering = ["order"]
        verbose_name = "Button"
        verbose_name_plural = "Buttons"