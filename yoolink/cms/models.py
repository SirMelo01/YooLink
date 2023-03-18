from django.db import models



class Text_Content(models.Model):
    text1 = models.CharField(max_length=1000, null=True)
    text2 = models.CharField(max_length=1000, null=True)