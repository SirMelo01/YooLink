from yoolink.ycms.applications.blog.services import render_markdown_to_html

for md in ["# Eins", "## Zwei", "### Drei", "#### Vier"]:
    print(repr(md), "->", render_markdown_to_html(md))
