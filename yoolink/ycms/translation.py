from modeltranslation.translator import register, TranslationOptions
from .models import FAQ, TextContent, fileentry, GaleryImage, Galerie

@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')  # Diese Felder sollen übersetzt werden

@register(TextContent)
class TextContentTranslationOptions(TranslationOptions):
    fields = ('header', 'title', 'description', 'buttonText')

@register(fileentry)
class FileEntryTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(GaleryImage)
class GaleryImageTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(Galerie)
class GalerieTranslationOptions(TranslationOptions):
    fields = ('title', 'description')