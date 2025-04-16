from modeltranslation.translator import register, TranslationOptions
from .models import FAQ, TextContent, fileentry, GaleryImage, Galerie, Button, PricingCard, PricingFeature

@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')

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

@register(Button)
class ButtonTranslationOptions(TranslationOptions):
    fields = ('text', 'hover_text')

@register(PricingCard)
class PricingCardTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(PricingFeature)
class PricingFeatureTranslationOptions(TranslationOptions):
    fields = ('text',)
