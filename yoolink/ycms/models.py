from django.db import models

# Create your models here.

from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save
from yoolink.users.models import User


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

class Blog(models.Model):
    title = models.CharField(max_length=255)
    title_image = models.ImageField(upload_to='yoolink/', default="", blank=True)
    date = models.DateField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    
    def __str__(self):
        return self.title + ' | ' + str(self.author)