import json
import re
from html import escape
from html.parser import HTMLParser

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


def build_default_code_from_markdown(markdown):
    markdown = (markdown or "").strip()
    if not markdown:
        return []

    return MarkdownToBlogCodeParser(markdown).parse()


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


def blog_code_to_markdown(code, body=""):
    try:
        blocks = normalize_blog_code(code, body)
    except (TypeError, ValueError, json.JSONDecodeError):
        return html_to_markdown(body)

    markdown_blocks = []
    for block in blocks:
        name = block.get("name")
        value = block.get("value") or ""

        if name == "title-1":
            markdown_blocks.append(f"## {strip_tags(value).strip()}")
        elif name == "title-2":
            markdown_blocks.append(f"### {strip_tags(value).strip()}")
        elif name == "title-3":
            markdown_blocks.append(f"#### {strip_tags(value).strip()}")
        elif name == "textArea":
            markdown_blocks.append(html_to_markdown(value))
        elif name == "image":
            attributes = block.get("attributes") or {}
            src = attributes.get("src") or ""
            alt = attributes.get("alt") or attributes.get("title") or ""
            if src:
                markdown_blocks.append(f"![{alt}]({src})")
        elif name == "code":
            language = _code_language(block)
            markdown_blocks.append(f"```{language}\n{value}\n```")
        else:
            rendered = render_blog_code_to_html([block])
            if rendered:
                markdown_blocks.append(rendered)

    markdown = "\n\n".join(block.strip() for block in markdown_blocks if block and block.strip())
    return markdown or html_to_markdown(body)


class MarkdownToBlogCodeParser:
    def __init__(self, markdown):
        self.lines = markdown.splitlines()
        self.blocks = []
        self.paragraph = []
        self.list_items = []
        self.in_code = False
        self.code_language = ""
        self.code_lines = []

    def parse(self):
        for line in self.lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                self._handle_code_fence(stripped)
                continue

            if self.in_code:
                self.code_lines.append(line)
                continue

            if not stripped:
                self._flush_paragraph()
                self._flush_list()
                continue

            image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
            if image:
                self._flush_paragraph()
                self._flush_list()
                self._append_image_block(image.group(1), image.group(2))
                continue

            heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading:
                self._flush_paragraph()
                self._flush_list()
                self._append_heading_block(len(heading.group(1)), heading.group(2))
                continue

            list_match = re.match(r"^(?:[-*]|\d+\.)\s+(.+)$", stripped)
            if list_match:
                self._flush_paragraph()
                self.list_items.append(list_match.group(1))
                continue

            if _is_raw_html_block(stripped):
                self._flush_paragraph()
                self._flush_list()
                self._append_text_block(line)
                continue

            self.paragraph.append(line)

        self._flush_paragraph()
        self._flush_list()

        if self.in_code:
            self._append_code_block()

        return self.blocks or build_default_code_from_html(render_markdown_to_html("\n".join(self.lines)))

    def _handle_code_fence(self, stripped):
        if self.in_code:
            self._append_code_block()
            self.in_code = False
            self.code_language = ""
            self.code_lines = []
            return

        self._flush_paragraph()
        self._flush_list()
        self.in_code = True
        self.code_language = stripped[3:].strip()
        self.code_lines = []

    def _flush_paragraph(self):
        if not self.paragraph:
            return

        text = " ".join(line.strip() for line in self.paragraph if line.strip())
        if text:
            self._append_text_block(f"<p>{_render_inline_markdown(text)}</p>")
        self.paragraph.clear()

    def _flush_list(self):
        if not self.list_items:
            return

        items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in self.list_items)
        self._append_text_block(f'<ul class="my-4 list-disc pl-6">{items}</ul>')
        self.list_items.clear()

    def _append_heading_block(self, level, text):
        clean_text = strip_tags(_render_inline_markdown(text)).strip()
        if not clean_text:
            return

        if level <= 2:
            self.blocks.append({
                "name": "title-1",
                "type": "h2",
                "attributes": {"class": "text-2xl mb-6 font-bold text-gray-900 lg:text-3xl"},
                "value": clean_text,
            })
        elif level == 3:
            self.blocks.append({
                "name": "title-2",
                "type": "h3",
                "attributes": {"class": "text-xl font-semibold my-4 lg:text-2xl"},
                "value": clean_text,
            })
        else:
            self.blocks.append({
                "name": "title-3",
                "type": "h4",
                "attributes": {"class": "text-lg font-medium my-4 lg:text-xl"},
                "value": clean_text,
            })

    def _append_text_block(self, value):
        value = (value or "").strip()
        if not value:
            return

        self.blocks.append({
            "name": "textArea",
            "type": "p",
            "attributes": {"class": "text-base my-4"},
            "value": value,
        })

    def _append_image_block(self, alt_text, src):
        src = (src or "").strip()
        if not src:
            return

        alt_text = (alt_text or "").strip()
        self.blocks.append({
            "name": "image",
            "type": "img",
            "attributes": {
                "src": src,
                "title": alt_text,
                "alt": alt_text,
                "class": "rounded-2xl my-4",
            },
            "css": {
                "height": "auto",
                "width": "100%",
            },
        })

    def _append_code_block(self):
        language_class = f" language-{self.code_language}" if self.code_language else ""
        self.blocks.append({
            "name": "code",
            "type": "code",
            "attributes": {
                "class": f"rounded-2xl my-4{language_class}",
                "data-prismjs-copy": "Copy",
            },
            "value": "\n".join(self.code_lines),
            "css": {
                "height": "auto",
                "width": "100%",
            },
        })


def _code_language(block):
    class_name = (block.get("attributes") or {}).get("class", "")
    for part in class_name.split():
        if part.startswith("language-"):
            return part.replace("language-", "", 1)
    return ""


def html_to_markdown(html):
    parser = SimpleHtmlToMarkdownParser()
    parser.feed(html or "")
    parser.close()
    return parser.get_markdown()


class SimpleHtmlToMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.link_stack = []
        self.list_depth = 0
        self.in_pre = False
        self.in_code = False
        self.code_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self._ensure_block()
            self.parts.append("#" * level + " ")
        elif tag == "p":
            self._ensure_block()
        elif tag == "br":
            self.parts.append("\n")
        elif tag in ("strong", "b"):
            self.parts.append("**")
        elif tag in ("em", "i"):
            self.parts.append("*")
        elif tag == "a":
            self.link_stack.append(attrs.get("href", ""))
            self.parts.append("[")
        elif tag == "img":
            alt = attrs.get("alt") or attrs.get("title") or ""
            src = attrs.get("src") or ""
            if src:
                self.parts.append(f"![{alt}]({src})")
        elif tag in ("ul", "ol"):
            self.list_depth += 1
            self._ensure_block()
        elif tag == "li":
            self._ensure_block()
            self.parts.append("  " * max(self.list_depth - 1, 0) + "- ")
        elif tag == "pre":
            self.in_pre = True
            self.code_buffer = []
            self._ensure_block()
        elif tag == "code" and self.in_pre:
            self.in_code = True
        elif tag == "code":
            self.parts.append("`")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._ensure_block()
        elif tag in ("strong", "b"):
            self.parts.append("**")
        elif tag in ("em", "i"):
            self.parts.append("*")
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            self.parts.append(f"]({href})" if href else "]")
        elif tag in ("ul", "ol"):
            self.list_depth = max(self.list_depth - 1, 0)
            self._ensure_block()
        elif tag == "li":
            self.parts.append("\n")
        elif tag == "code" and self.in_pre:
            self.in_code = False
        elif tag == "code":
            self.parts.append("`")
        elif tag == "pre":
            code = "".join(self.code_buffer).strip("\n")
            self.parts.append(f"```\n{code}\n```")
            self.code_buffer = []
            self.in_pre = False
            self._ensure_block()

    def handle_data(self, data):
        if self.in_pre:
            self.code_buffer.append(data)
        else:
            self.parts.append(data)

    def get_markdown(self):
        markdown = "".join(self.parts)
        markdown = re.sub(r"[ \t]+\n", "\n", markdown)
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return markdown.strip()

    def _ensure_block(self):
        current = "".join(self.parts)
        if current and not current.endswith("\n\n"):
            if current.endswith("\n"):
                self.parts.append("\n")
            else:
                self.parts.append("\n\n")


def render_markdown_to_html(markdown):
    markdown = (markdown or "").strip()
    if not markdown:
        return ""

    lines = markdown.splitlines()
    html = []
    paragraph = []
    list_items = []
    in_code = False
    code_language = ""
    code_lines = []

    def flush_paragraph():
        if paragraph:
            text = " ".join(line.strip() for line in paragraph if line.strip())
            if text:
                html.append(f'<p class="text-base my-4">{_render_inline_markdown(text)}</p>')
            paragraph.clear()

    def flush_list():
        if list_items:
            items = "".join(f"<li>{_render_inline_markdown(item)}</li>" for item in list_items)
            html.append(f'<ul class="my-4 list-disc pl-6">{items}</ul>')
            list_items.clear()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                language_class = f" language-{escape(code_language)}" if code_language else ""
                code = escape("\n".join(code_lines))
                html.append(
                    f'<pre class="my-4 rounded-2xl"><code class="{language_class.strip()}">{code}</code></pre>'
                )
                in_code = False
                code_language = ""
                code_lines = []
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_language = stripped[3:].strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            flush_paragraph()
            flush_list()
            alt_text = escape(image.group(1), quote=True)
            src = escape(image.group(2), quote=True)
            html.append(f'<img src="{src}" alt="{alt_text}" class="rounded-2xl my-4">')
            continue

        if _is_raw_html_block(stripped):
            flush_paragraph()
            flush_list()
            html.append(line)
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = min(len(heading.group(1)), 6)
            classes = {
                1: "text-3xl font-bold my-6",
                2: "text-2xl mb-6 font-bold text-gray-900 lg:text-3xl",
                3: "text-xl font-semibold my-4 lg:text-2xl",
                4: "text-lg font-medium my-4 lg:text-xl",
            }.get(level, "text-base font-semibold my-4")
            html.append(f'<h{level} class="{classes}">{_render_inline_markdown(heading.group(2))}</h{level}>')
            continue

        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            list_items.append(list_match.group(1))
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_list()

    if in_code:
        code = escape("\n".join(code_lines))
        html.append(f'<pre class="my-4 rounded-2xl"><code>{code}</code></pre>')

    return "\n".join(html)


def _is_raw_html_block(line):
    return bool(re.match(r"^</?(div|iframe|video|img|a|pre|code|figure|table|section|article)\b", line, re.I))


def _render_inline_markdown(text):
    placeholders = []

    def stash(value):
        placeholders.append(value)
        return f"@@MD{len(placeholders) - 1}@@"

    escaped = escape(text)
    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: stash(
        f'<img src="{escape(m.group(2), quote=True)}" alt="{escape(m.group(1), quote=True)}">'
    ), escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: stash(
        f'<a class="text-blue-500 hover:text-blue-600" href="{escape(m.group(2), quote=True)}">{m.group(1)}</a>'
    ), escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    for index, value in enumerate(placeholders):
        escaped = escaped.replace(f"@@MD{index}@@", value)

    return escaped


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
