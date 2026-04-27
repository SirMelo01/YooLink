from django.db import models

# Create your models here.
from django.db.models import Q
from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save
from yoolink.users.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import get_language, gettext_lazy as _

from yoolink.ycms.applications.shop.models import Order
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

def upload_to_product_image(instance, filename):
    media_uuid = getattr(instance, "media_uuid", None)
    identifier = media_uuid or getattr(instance, "id", "tmp")
    return f"yoolink/products/{identifier}/{filename}"

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
    place = models.CharField(max_length=60, default="")
    autoplay = models.BooleanField(default=False, help_text="Video automatisch abspielen?")
    muted = models.BooleanField(default=False, help_text="Video stumm starten?")
    loop = models.BooleanField(default=False, help_text="Video in Endlosschleife?")
    playsinline = models.BooleanField(default=True, help_text="Video inline abspielen (bes. für iOS)?")
    show_controls = models.BooleanField(default=True, help_text="Standard Video Controls anzeigen?")
    preload = models.CharField(
        max_length=20,
        choices=[('auto', 'Auto'), ('metadata', 'Nur Metadaten'), ('none', 'Nichts')],
        default='metadata',
        help_text="Preload-Verhalten beim Seitenladen"
    )

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

    language = models.CharField(
        max_length=10,
        default='de',
        choices=[
            ('de', 'Deutsch'),
            ('en', 'English'),
            ('fr', 'Französisch'),
            # weitere Sprachen bei Bedarf
        ]
    )

    original = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='translations',
        help_text=_("Bezieht sich auf den Original-Blog (z.B. auf Deutsch)")
    )

    def delete(self, *args, **kwargs):
        self.title_image.storage.delete(self.title_image.name)
        super(Blog, self).delete(*args, **kwargs)
    
    def __str__(self):
        return self.title + ' | ' + str(self.author)
    
    def save(self, *args, **kwargs):
        if not self.original:
            # Nur Original-Blogs bekommen einen Slug
            self.slug = slugify(self.title)

        super(Blog, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:blog-detail", kwargs={"pk": self.pk, "slug_title": self.slug})

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

# Notifications
class NotificationQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(seen=False, is_spam=False)

    def latest_first(self):
        return self.order_by('-created_at')

    def not_spam(self):
        return self.filter(is_spam=False)

    def spam(self):
        return self.filter(is_spam=True)

class Notification(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Niedrig'
        NORMAL = 'normal', 'Normal'
        HIGH = 'high', 'Hoch'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_spam = models.BooleanField(default=False)

    # Optionaler Link zu Message
    message = models.ForeignKey(
        Message,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications'
    )

    order = models.ForeignKey(
        Order,
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='notifications'
    )

    # Optionaler freier Link (falls keine Message)
    link_url = models.URLField(blank=True, default='')

    objects = NotificationQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['seen']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_spam'])
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

    def get_absolute_url(self):
        return reverse('cms:notification-detail', args=[self.pk])
    
    @property
    def has_target(self) -> bool:
        return bool(self.message_id or self.link_url)

    @property
    def external_target_url(self) -> str:
        # Falls du eine Message-Detailseite hast, hier anpassen.
        return self.link_url or ''


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
    vacation_start = models.DateTimeField(null=True, blank=True)
    vacation_end   = models.DateTimeField(null=True, blank=True)
    global_font = models.CharField(max_length=60, default='font-sans')
    logo = models.ImageField(upload_to=upload_to_user_settings, default="", blank=True)
    favicon = models.ImageField(upload_to=upload_to_user_settings, default="", blank=True)

    two_factor_email_enabled = models.BooleanField(default=False)
    two_factor_email_verified = models.BooleanField(default=False)
    two_factor_email_code = models.CharField(max_length=6, blank=True, default='')
    two_factor_email_code_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(two_factor_email_enabled=False) | ~Q(email=''),
                name='two_factor_requires_email',
            ),
        ]

    def __str__(self):
        return f"{self.full_name}'s Einstellungen"
    
    def clean(self):
        if self.vacation_start and self.vacation_end and self.vacation_start > self.vacation_end:
            raise ValidationError("Urlaubsbeginn darf nicht nach dem Urlaubsende liegen.")

        if self.two_factor_email_enabled and not (self.email or '').strip():
            raise ValidationError("Für die E-Mail-2FA muss eine E-Mail-Adresse hinterlegt sein.")
        
    def is_vacation_banner_active(self):
        """true, wenn Toggle an UND wir innerhalb des optionalen Zeitfensters sind."""
        if not self.vacation:
            return False
        now = timezone.now()
        if self.vacation_start and self.vacation_end:
            return self.vacation_start <= now <= self.vacation_end
        if self.vacation_start and not self.vacation_end:
            return now >= self.vacation_start
        if not self.vacation_start and self.vacation_end:
            return now <= self.vacation_end
        return True  # kein Fenster gesetzt -> sichtbar solange Toggle an

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

    display_order = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.full_name
    
    class Meta:
        ordering = ["display_order", "id"]
    
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