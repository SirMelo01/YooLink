import re

from django.db import models
from django.urls import reverse
from django.utils.html import escape
from django.utils.text import slugify


class TextContent(models.Model):
    name = models.CharField(max_length=50, default="", unique=True)
    header = models.CharField(max_length=100, default="")
    title = models.CharField(max_length=140, default="")
    description = models.TextField(default="")
    buttonText = models.CharField(max_length=120, default="")

    class Meta:
        db_table = "ycms_textcontent"


class PrivacyPolicy(models.Model):
    use_html = models.BooleanField(default=False)
    content_text = models.TextField(default="", blank=True)
    content_html = models.TextField(default="", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    TOKENS = {
        "OWNER_NAME": "owner_name",
        "ADDRESS": "address",
        "EMAIL": "email",
        "TEL": "tel_number",
        "FAX": "fax_number",
        "MOBILE": "mobile_number",
        "WEBSITE": "website",
    }

    RESPONSIBLE_SECTION_HTML = (
        "<h3>Hinweis zur verantwortlichen Stelle</h3>"
        "<p>Die verantwortliche Stelle fÃ¼r die Datenverarbeitung auf dieser Website ist:</p>"
        "<p>[[OWNER_NAME]]<br />[[ADDRESS]]</p>"
        "<p>Telefon: [[TEL]]<br />E-Mail: [[EMAIL]]</p>"
        "<p>Verantwortliche Stelle ist die natuerliche oder juristische Person, die allein "
        "oder gemeinsam mit anderen Ã¼ber die Zwecke und Mittel der Verarbeitung von personenbezogenen "
        "Daten (z. B. Namen, E-Mail-Adressen o. A.) entscheidet.</p>"
    )

    RESPONSIBLE_SECTION_TEXT = (
        "Hinweis zur verantwortlichen Stelle\n"
        "Die verantwortliche Stelle fÃ¼r die Datenverarbeitung auf dieser Website ist:\n"
        "[[OWNER_NAME]]\n"
        "[[ADDRESS]]\n"
        "Telefon: [[TEL]]\n"
        "E-Mail: [[EMAIL]]\n"
        "Verantwortliche Stelle ist die natuerliche oder juristische Person, die allein oder gemeinsam "
        "mit anderen Ã¼ber die Zwecke und Mittel der Verarbeitung von personenbezogenen Daten (z. B. Namen, "
        "E-Mail-Adressen o. A.) entscheidet."
    )

    class Meta:
        db_table = "ycms_privacypolicy"

    @staticmethod
    def _owner_name(owner_data):
        if not owner_data:
            return ""
        return (
            getattr(owner_data, "company_name", "")
            or getattr(owner_data, "owner_name", "")
            or getattr(owner_data, "full_name", "")
            or ""
        ).strip()

    @staticmethod
    def _owner_value(owner_data, attr):
        if not owner_data:
            return ""
        return str(getattr(owner_data, attr, "") or "").strip()

    @classmethod
    def _token_values(cls, owner_data):
        if not owner_data:
            return {
                "OWNER_NAME": "",
                "ADDRESS": "",
                "EMAIL": "",
                "TEL": "",
                "FAX": "",
                "MOBILE": "",
                "WEBSITE": "",
            }

        return {
            "OWNER_NAME": cls._owner_name(owner_data),
            "ADDRESS": cls._owner_value(owner_data, "address"),
            "EMAIL": cls._owner_value(owner_data, "email"),
            "TEL": cls._owner_value(owner_data, "tel_number"),
            "FAX": cls._owner_value(owner_data, "fax_number"),
            "MOBILE": cls._owner_value(owner_data, "mobile_number"),
            "WEBSITE": cls._owner_value(owner_data, "website"),
        }

    @classmethod
    def _format_token_value(cls, token, value, as_html=False):
        if not value:
            return ""

        if not as_html:
            return value

        escaped_value = str(escape(value))
        if token == "ADDRESS":
            return escaped_value.replace("\n", "<br />")
        return escaped_value

    @classmethod
    def replace_tokens(cls, content, owner_data, as_html=False):
        if not content:
            return content

        token_values = cls._token_values(owner_data)
        for token, value in token_values.items():
            content = content.replace(f"[[{token}]]", cls._format_token_value(token, value, as_html))
        return content

    @classmethod
    def tokenize_content(cls, content, owner_data):
        if not content or not owner_data:
            return content

        owner_name = cls._owner_name(owner_data)
        replacements = [
            (owner_name, "OWNER_NAME"),
            (cls._owner_value(owner_data, "address"), "ADDRESS"),
            (cls._owner_value(owner_data, "email"), "EMAIL"),
            (cls._owner_value(owner_data, "tel_number"), "TEL"),
            (cls._owner_value(owner_data, "fax_number"), "FAX"),
            (cls._owner_value(owner_data, "mobile_number"), "MOBILE"),
            (cls._owner_value(owner_data, "website"), "WEBSITE"),
        ]

        for attr in ("company_name", "owner_name", "full_name"):
            value = cls._owner_value(owner_data, attr)
            if value:
                replacements.append((value, "OWNER_NAME"))

        for value, token in replacements:
            if value and len(value) >= 3:
                content = content.replace(value, f"[[{token}]]")
                content = content.replace(str(escape(value)), f"[[{token}]]")
        return content

    @classmethod
    def ensure_responsible_section(cls, content, as_html):
        if not content:
            return content

        if "[[OWNER_NAME]]" in content or "[[EMAIL]]" in content or "[[ADDRESS]]" in content:
            return content

        appendix = cls.RESPONSIBLE_SECTION_HTML if as_html else cls.RESPONSIBLE_SECTION_TEXT
        return f"{content}\n\n{appendix}"

    @staticmethod
    def text_to_html(text):
        if not text:
            return ""

        blocks = [block.strip() for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
        html_blocks = []
        for block in blocks:
            escaped_block = escape(block).replace("\n", "<br />")
            html_blocks.append(f"<p>{escaped_block}</p>")
        return "\n".join(html_blocks)

    def render_content(self, owner_data):
        if self.use_html:
            content = self.replace_tokens(self.content_html, owner_data, as_html=True)
            return content

        content = self.replace_tokens(self.content_text, owner_data)
        return self.text_to_html(content)

    @classmethod
    def prepare_content(cls, raw, owner_data, as_html):
        content = (raw or "").strip()
        content = cls.tokenize_content(content, owner_data)
        content = cls.ensure_responsible_section(content, as_html)
        return content


class ImpressumBlock(models.Model):
    """
    Ein frei konfigurierbarer Inhalts-Block für das Impressum (Builder).

    Die rechtlichen Stammdaten (Unternehmen, Inhaber, Anschrift, Kontakt) werden
    direkt aus den Unternehmensdaten (WebsiteSettings) gezogen. Diese Blöcke
    bilden den frei pflegbaren Rest (Haftungshinweis, Copyright, eigene Abschnitte).

    Im `content` werden unterstützt:
      * Platzhalter wie [[COMPANY]], [[OWNER_NAME]], [[ADDRESS]] (aus den Unternehmensdaten)
      * **fett** für fettgedruckten Text
      * Leerzeilen = neue Absätze, einfache Zeilenumbrüche bleiben erhalten
    """

    title = models.CharField(max_length=200, default="", blank=True)
    content = models.TextField(default="", blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    TOKENS = {
        "COMPANY": "company_name",
        "OWNER_NAME": "owner_name",
        "ADDRESS": "address",
        "EMAIL": "email",
        "TEL": "tel_number",
        "FAX": "fax_number",
        "MOBILE": "mobile_number",
        "WEBSITE": "website",
        "COUNTRY": "address_country",
    }

    class Meta:
        db_table = "ycms_impressumblock"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title or f"Impressum-Block #{self.pk}"

    @staticmethod
    def _owner_value(owner_data, attr):
        if not owner_data:
            return ""
        return str(getattr(owner_data, attr, "") or "").strip()

    @classmethod
    def _render_inline(cls, text, owner_data):
        # Erst alles escapen, danach Platzhalter durch (escapte) Stammdaten ersetzen.
        out = escape(text)
        for token, attr in cls.TOKENS.items():
            out = out.replace(f"[[{token}]]", str(escape(cls._owner_value(owner_data, attr))))
        # **fett** -> <strong>
        out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
        return out

    def render_html(self, owner_data):
        """Rendert den Block-Inhalt zu sicherem HTML (Absätze + Zeilenumbrüche)."""
        text = (self.content or "").strip()
        if not text:
            return ""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        html_parts = []
        for paragraph in paragraphs:
            inner = self._render_inline(paragraph, owner_data).replace("\n", "<br />")
            html_parts.append(f"<p>{inner}</p>")
        return "\n".join(html_parts)


def _generate_unique_customer_slug(instance, base_slug):
    slug = slugify(base_slug or "kunde") or "kunde"
    unique_slug = slug
    counter = 2
    queryset = Customer.objects.filter(slug=unique_slug)
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.exists():
        unique_slug = f"{slug}-{counter}"
        queryset = Customer.objects.filter(slug=unique_slug)
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        counter += 1
    return unique_slug


class Customer(models.Model):
    SECTION_REFERENCES = "references"
    SECTION_SPECIAL = "special"

    SECTION_CHOICES = [
        (SECTION_REFERENCES, "Referenzen / Kunden"),
        (SECTION_SPECIAL, "Spezielle Programmierungen"),
    ]

    LOGO_STYLE_CIRCLE = "circle"
    LOGO_STYLE_SQUARE = "square"
    LOGO_STYLE_WIDE = "wide"
    LOGO_STYLE_TEXT = "text"

    LOGO_STYLE_CHOICES = [
        (LOGO_STYLE_CIRCLE, "Logo rund (kompakt)"),
        (LOGO_STYLE_SQUARE, "Logo quadratisch (kompakt)"),
        (LOGO_STYLE_WIDE, "Logo breit (mit integriertem Text)"),
        (LOGO_STYLE_TEXT, "Nur Text/Initialen (kein Logo)"),
    ]

    name = models.CharField(max_length=160, default="")
    subtitle = models.CharField(max_length=200, blank=True, default="")
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    website_url = models.URLField(blank=True, default="")
    website_display = models.CharField(max_length=200, blank=True, default="")
    published_date = models.DateField(null=True, blank=True)

    section = models.CharField(
        max_length=20, choices=SECTION_CHOICES, default=SECTION_REFERENCES
    )

    short_description = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    services_text = models.TextField(blank=True, default="")
    testimonial = models.TextField(blank=True, default="")
    testimonial_author = models.CharField(max_length=160, blank=True, default="")

    title_image = models.ForeignKey(
        "ycms.fileentry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_title_images",
    )
    banner_image = models.ForeignKey(
        "ycms.fileentry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_banner_images",
    )
    logo = models.ForeignKey(
        "ycms.fileentry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_logos",
    )
    gallery = models.ForeignKey(
        "ycms.Galerie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )

    logo_style = models.CharField(
        max_length=10, choices=LOGO_STYLE_CHOICES, default=LOGO_STYLE_CIRCLE
    )
    logo_fallback_text = models.CharField(max_length=8, blank=True, default="")

    active = models.BooleanField(default=True)
    show_detail_page = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ycms_customer"
        ordering = ["order", "-published_date", "id"]

    def __str__(self):
        return self.name or f"Customer #{self.pk}"

    def save(self, *args, **kwargs):
        base = self.slug or self.name
        self.slug = _generate_unique_customer_slug(self, base)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("kunde-detail", kwargs={"slug": self.slug})

    @property
    def has_detail(self):
        return self.active and self.show_detail_page
