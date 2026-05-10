from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def responsive_image_attrs(image_entry, sizes="100vw"):
    """
    Render srcset/sizes attributes for CMS fileentry images when a mobile
    variant exists. Returns an empty string for older images and other models.
    """
    if not image_entry:
        return ""

    srcset = getattr(image_entry, "responsive_srcset", "")
    if callable(srcset):
        srcset = srcset()

    if not srcset:
        return ""

    return format_html('srcset="{}" sizes="{}"', srcset, sizes)


@register.simple_tag
def responsive_image_srcset(image_entry):
    if not image_entry:
        return ""

    srcset = getattr(image_entry, "responsive_srcset", "")
    if callable(srcset):
        srcset = srcset()

    return srcset or ""
