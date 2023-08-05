from django.db import models

# Create your models here.

from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save
from yoolink.users.models import User
from django.utils.text import slugify


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
class fileentry(models.Model):
    file = models.ImageField(upload_to='yoolink/')
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

class GaleryImage(models.Model):
    upload = models.ImageField(upload_to='yoolink/galery/',)
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
    active = models.BooleanField(default=False)
    images = models.ManyToManyField(GaleryImage)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

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
    description = models.CharField(max_length=700, default="")
    buttonText = models.CharField(max_length=60, default="")

