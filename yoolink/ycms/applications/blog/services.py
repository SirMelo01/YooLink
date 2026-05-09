import json
import re
from html import escape

from django.utils.html import strip_tags


ALLOWED_ATTR_RE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9:._-]*$")


def build_default_code_from_html(body):
    body = (body or "").strip()
    if not body:
        return []

    return [
        {
            "name": "textArea",
            "type": "p",
            "attributes": {"class": "text-base my-4"},
            "value": body,
        }
    ]


def normalize_blog_code(value, body=""):
    if value in (None, "", {}, []):
        return build_default_code_from_html(body)

    if isinstance(value, str):
        value = json.loads(value)

    if isinstance(value, dict):
        if isinstance(value.get("blocks"), list):
            value = value["blocks"]
        else:
            value = [value]

    if not isinstance(value, list):
        raise ValueError("code muss eine JSON-Liste oder ein Objekt sein.")

    return value


def strip_generated_blog_intro(body, title, description):
    body = body or ""
    title = (title or "").strip()
    description = (description or "").strip()

    if not body or not title:
        return body

    prefix_match = re.match(r"^\s*<div\b[^>]*>", body, flags=re.IGNORECASE)
    suffix = "</div>" if body.rstrip().lower().endswith("</div>") else ""
    prefix = prefix_match.group(0) if prefix_match else ""
    rest = body[len(prefix):]
    if suffix:
        rest = rest[: -len(suffix)]

    def remove_leading_tag(html, tag_name, expected_text):
        expected_text = (expected_text or "").strip()
        if not expected_text:
            return html

        tag_match = re.match(
            rf"^\s*<{tag_name}\b[^>]*>.*?</{tag_name}>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not tag_match:
            return html

        tag_html = tag_match.group(0)
        tag_text = " ".join(strip_tags(tag_html).split())
        if tag_text == " ".join(expected_text.split()):
            return html[tag_match.end():]

        return html

    rest = remove_leading_tag(rest, "h1", title)
    rest = remove_leading_tag(rest, "p", description)
    return prefix + rest + suffix


def render_blog_code_to_html(code):
    blocks = normalize_blog_code(code)
    rendered = []

    for block in blocks:
        name = block.get("name")
        tag_name = block.get("type") or "div"

        if name == "galery":
            tag_name = "div"
        elif name == "code":
            tag_name = "code"

        if not ALLOWED_ATTR_RE.match(tag_name):
            tag_name = "div"

        attrs = _render_attrs(block.get("attributes") or {}, block.get("css") or {})
        value = block.get("value") or ""

        if name == "image":
            rendered.append(f"<img{attrs}>")
        elif name == "code":
            rendered.append(f"<pre><code{attrs}>{escape(value)}</code></pre>")
        elif name == "galery":
            rendered.append(_render_gallery(block, attrs))
        elif tag_name == "iframe":
            rendered.append(f"<iframe{attrs}></iframe>")
        else:
            rendered.append(f"<{tag_name}{attrs}>{value}</{tag_name}>")

    return "\n".join(rendered)


def _render_attrs(attributes, css):
    rendered = []

    for key, value in attributes.items():
        if value is None or value is False or not ALLOWED_ATTR_RE.match(str(key)):
            continue

        if value is True:
            rendered.append(f" {key}")
        else:
            rendered.append(f' {key}="{escape(str(value), quote=True)}"')

    if css:
        style = "; ".join(
            f"{key}: {value}"
            for key, value in css.items()
            if ALLOWED_ATTR_RE.match(str(key)) and value not in (None, "")
        )
        if style:
            rendered.append(f' style="{escape(style, quote=True)}"')

    return "".join(rendered)


def _render_gallery(block, attrs):
    images = block.get("images") or []
    image_class = block.get("imageClass") or "w-full rounded-xl"
    image_html = "".join(
        f'<div><img src="{escape(str(url), quote=True)}" class="{escape(image_class, quote=True)}"></div>'
        for url in images
        if url
    )
    return f"<div{attrs}>{image_html}</div>"
