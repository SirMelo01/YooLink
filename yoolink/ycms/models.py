from django.db import models

# Create your models here.

from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save
from yoolink.users.models import User
from django.utils.text import slugify
from django.utils import timezone


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
    slug = models.SlugField(unique=True, default='default-slug')
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
    

""" 
Products
"""
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=200) 
    slug = models.SlugField(unique=True)
    
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
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    title_image = models.ImageField(upload_to=upload_to_product_image, default="", blank=True)
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


class OrderItem(models.Model):
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

class Order(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Offen'),
        ('PAID', 'Bezahlt'),
        ('COMPLETED', 'Abgeschlossen'),
    ]

    items = models.ManyToManyField(OrderItem)
    buyer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Order - {self.buyer_email} - {self.status}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=255)
    email = models.EmailField()
    comment = models.TextField()
    rating = models.PositiveIntegerField(default=5)  # Assuming a rating out of 5

    def __str__(self):
        return f"{self.user_name} - {self.product.title} - {self.rating} stars"


"""
Messages
"""

class Message(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=60)
    message = models.CharField(max_length=600)
    date = models.DateField()
    seen = models.BooleanField(default=False)


class TextContent(models.Model):
    name = models.CharField(max_length=50, default="", unique=True)
    header = models.CharField(max_length=50, default="")
    title = models.CharField(max_length=70, default="")
    description = models.TextField(default="")
    buttonText = models.CharField(max_length=60, default="")

