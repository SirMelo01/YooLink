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

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Slugify the title and store it in the slug field
        self.slug = slugify(self.title)

        # Call the parent class's save method to actually save the model
        super(Product, self).save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Offen'),
        ('PAID', 'Bezahlt'),
        ('READY_FOR_PICKUP', 'Bereit zur Abholung'),
        ('SHIPPED', 'Versendet'),
        ('COMPLETED', 'Abgeschlossen'),
    ]
    PAYMENT_CHOICES = [
        ('INVOICE', 'Rechnung'),
        ('PICKUP', 'Zahlung bei Abholung'),
    ]

    buyer_email = models.EmailField()
    buyer_address = models.TextField(default='')
    verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    payment = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='INVOICE')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]
    
    def get_payment_display(self):
        return dict(self.PAYMENT_CHOICES)[self.payment]

    def total(self):
        return sum(item.subtotal() for item in self.orderitem_set.all())  # Adjusted to use the related name orderitem_set

    def total_with_tax(self):
        return self.total() + self.calculate_tax()

    def calculate_tax(self):
        return self.total() * 0.19

    def __str__(self):
        return f"Order #{self.pk} - {self.buyer_email} - {self.status}"

    def total_quantity(self):
        return sum(item.quantity for item in self.orderitem_set.all())  # Adjusted to use the related name orderitem_set


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
    message = models.CharField(max_length=600)
    date = models.DateField(auto_now_add=True, null=True)
    seen = models.BooleanField(default=False)


class TextContent(models.Model):
    name = models.CharField(max_length=50, default="", unique=True)
    header = models.CharField(max_length=50, default="")
    title = models.CharField(max_length=70, default="")
    description = models.TextField(default="")
    buttonText = models.CharField(max_length=60, default="")


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, default='')
    full_name = models.CharField(max_length=255, default='')
    company_name = models.CharField(max_length=255, default='')
    tel_number = models.CharField(max_length=18, default='')
    fax_number = models.CharField(max_length=18, default='')
    mobile_number = models.CharField(max_length=18, default='')
    website = models.URLField(blank=True, default='')

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
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opening_hours')
    day = models.CharField(max_length=3, choices=DAY_CHOICES, unique=True)
    is_open = models.BooleanField(default=False)
    start_time = models.TimeField(default='08:00')  # Set default start time to 8 o'clock
    end_time = models.TimeField(default='14:00')    # Set default end time to 14 o'clock
    has_lunch_break = models.BooleanField(default=False)
    lunch_break_start = models.TimeField(blank=True, null=True)
    lunch_break_end = models.TimeField(blank=True, null=True)

    def get_day(self):
        return dict(self.DAY_CHOICES)[self.day]

    def __str__(self):
        return f"Opening hours for {self.user.username} on {self.get_day_display()}"