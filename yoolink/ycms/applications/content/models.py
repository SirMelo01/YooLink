import re

from django.db import models
from django.utils.html import escape


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
    def _owner_name(user_settings):
        if not user_settings:
            return ""
        return (user_settings.company_name or user_settings.full_name or "").strip()

    @classmethod
    def _token_values(cls, user_settings):
        if not user_settings:
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
            "OWNER_NAME": cls._owner_name(user_settings),
            "ADDRESS": (user_settings.address or "").strip(),
            "EMAIL": (user_settings.email or "").strip(),
            "TEL": (user_settings.tel_number or "").strip(),
            "FAX": (user_settings.fax_number or "").strip(),
            "MOBILE": (user_settings.mobile_number or "").strip(),
            "WEBSITE": (user_settings.website or "").strip(),
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
    def replace_tokens(cls, content, user_settings, as_html=False):
        if not content:
            return content

        token_values = cls._token_values(user_settings)
        for token, value in token_values.items():
            content = content.replace(f"[[{token}]]", cls._format_token_value(token, value, as_html))
        return content

    @classmethod
    def tokenize_content(cls, content, user_settings):
        if not content or not user_settings:
            return content

        owner_name = cls._owner_name(user_settings)
        replacements = [
            (owner_name, "OWNER_NAME"),
            ((user_settings.address or "").strip(), "ADDRESS"),
            ((user_settings.email or "").strip(), "EMAIL"),
            ((user_settings.tel_number or "").strip(), "TEL"),
            ((user_settings.fax_number or "").strip(), "FAX"),
            ((user_settings.mobile_number or "").strip(), "MOBILE"),
            ((user_settings.website or "").strip(), "WEBSITE"),
        ]

        if user_settings.company_name:
            replacements.append((user_settings.company_name.strip(), "OWNER_NAME"))
        if user_settings.full_name:
            replacements.append((user_settings.full_name.strip(), "OWNER_NAME"))

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

    def render_content(self, user_settings):
        if self.use_html:
            content = self.replace_tokens(self.content_html, user_settings, as_html=True)
            return content

        content = self.replace_tokens(self.content_text, user_settings)
        return self.text_to_html(content)

    @classmethod
    def prepare_content(cls, raw, user_settings, as_html):
        content = (raw or "").strip()
        content = cls.tokenize_content(content, user_settings)
        content = cls.ensure_responsible_section(content, as_html)
        return content

