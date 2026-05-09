from modeltranslation.translator import TranslationOptions, register

from .models import TextContent


@register(TextContent)
class TextContentTranslationOptions(TranslationOptions):
    fields = ("header", "title", "description", "buttonText")

