from modeltranslation.translator import TranslationOptions, register

from .models import Customer, TextContent


@register(TextContent)
class TextContentTranslationOptions(TranslationOptions):
    fields = ("header", "title", "description", "buttonText")


@register(Customer)
class CustomerTranslationOptions(TranslationOptions):
    fields = (
        "subtitle",
        "short_description",
        "description",
        "services_text",
        "testimonial",
        "testimonial_author",
    )

