from django.db import models



class Text_Content(models.Model):
    text1 = models.CharField(max_length=1000, null=True)
    text2 = models.CharField(max_length=1000, null=True)
    bild = models.ImageField(upload_to='media', null=True)


class Galerie(models.Model):
    file = models.FileField(upload_to='files')