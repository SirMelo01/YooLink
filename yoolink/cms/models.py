from django.db import models
import os
from PIL import Image
from django.db.models.signals import post_save


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


#def image_compressor(sender, **kwargs): 
#    if kwargs["created"]:
#        with Image.open(kwargs["instance"].file.path) as file:
#            file.save(kwargs["instance"].file.path, optimize=True, quality=10)

#post_save.connect(image_compressor, sender=fileentry)

    
class Text_Content(models.Model):
    text1 = models.CharField(max_length=1000, null=True)
    text2 = models.CharField(max_length=1000, null=True)
    bild = models.ImageField(upload_to='media', null=True)


class Galerie(models.Model):
    file = models.FileField(upload_to='files')