from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from yoolink.users.tests.factories import UserFactory
from yoolink.ycms.models import Blog, DeveloperApiKey, UserSettings, fileentry

pytestmark = pytest.mark.django_db


@pytest.fixture
def cms_user():
    user = UserFactory(email="api-owner@example.com")
    user.set_password("password12345")
    user.save(update_fields=["password", "email"])
    UserSettings.objects.create(
        user=user,
        email=user.email,
        full_name="API Owner",
        company_name="YooLink Test",
    )
    return user


def issue_key(user, access_level=DeveloperApiKey.WRITE, expires_at=None):
    return DeveloperApiKey.issue_key(
        created_by=user,
        name="Content Automation",
        access_level=access_level,
        allowed_apps=[DeveloperApiKey.APP_BLOG],
        expires_at=expires_at,
    )


def api_client_for(raw_key):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw_key}")
    return client


def image_upload(name="blog-image.png"):
    buffer = BytesIO()
    Image.new("RGB", (16, 16), color="blue").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def test_developer_settings_creates_one_time_api_key(client, cms_user):
    client.force_login(cms_user)

    response = client.post(
        reverse("ycms:developer-settings"),
        {
            "action": "create",
            "name": "External AI Platform",
            "access_level": DeveloperApiKey.WRITE,
            "allowed_apps": [DeveloperApiKey.APP_BLOG],
            "expires_in": "never",
        },
    )

    assert response.status_code == 200
    assert DeveloperApiKey.objects.filter(created_by=cms_user).count() == 1
    assert b"yl_live_" in response.content
    assert reverse("ycms:developer-api-docs").encode() in response.content


def test_developer_api_docs_requires_login_and_documents_blog_api(client, cms_user):
    response = client.get(reverse("ycms:developer-api-docs"))
    assert response.status_code == 302

    client.force_login(cms_user)
    response = client.get(reverse("ycms:developer-api-docs"))

    assert response.status_code == 200
    assert b"/api/cms/blog/" in response.content
    assert b"Authorization: Bearer" in response.content
    assert b"POST" in response.content


def test_read_only_key_can_read_blogs_but_cannot_create(cms_user):
    Blog.objects.create(
        title="Existing Blog",
        description="Existing description",
        body="<p>Existing body</p>",
        code=[],
        active=True,
        author=cms_user,
    )
    _, raw_key = issue_key(cms_user, access_level=DeveloperApiKey.READ)
    client = api_client_for(raw_key)

    list_response = client.get("/api/cms/blog/")
    create_response = client.post(
        "/api/cms/blog/",
        {
            "title": "Blocked Blog",
            "description": "Should not be created",
            "body": "<p>Nope</p>",
        },
        format="json",
    )

    assert list_response.status_code == 200
    assert list_response.data[0]["title"] == "Existing Blog"
    assert "body" not in list_response.data[0]
    assert "markdown" not in list_response.data[0]
    assert "code" not in list_response.data[0]
    assert "translations" not in list_response.data[0]
    assert list_response.data[0]["api_url"].endswith(f"/api/cms/blog/{Blog.objects.get().id}/")
    assert create_response.status_code == 403
    assert not Blog.objects.filter(title="Blocked Blog").exists()


def test_write_key_creates_and_updates_blog(cms_user):
    _, raw_key = issue_key(cms_user)
    client = api_client_for(raw_key)

    create_response = client.post(
        "/api/cms/blog/",
        {
            "title": "KI Event Rueckblick",
            "description": "Automatisch erzeugter Rueckblick.",
            "body": "<p>Der Event war stark besucht.</p>",
            "active": True,
            "language": "de",
        },
        format="json",
    )

    assert create_response.status_code == 201
    blog = Blog.objects.get(title="KI Event Rueckblick")
    assert blog.author == cms_user
    assert blog.active is True
    assert blog.code[0]["name"] == "textArea"

    update_response = client.patch(
        f"/api/cms/blog/{blog.id}/",
        {"active": False, "description": "Aktualisierte Beschreibung."},
        format="json",
    )

    assert update_response.status_code == 200
    blog.refresh_from_db()
    assert blog.active is False
    assert blog.description == "Aktualisierte Beschreibung."


def test_write_key_can_create_blog_from_markdown(cms_user):
    _, raw_key = issue_key(cms_user)
    client = api_client_for(raw_key)

    response = client.post(
        "/api/cms/blog/",
        {
            "title": "Markdown Blog",
            "description": "Markdown Beschreibung.",
            "markdown": "## Einleitung\n\nDas ist **fett** und [verlinkt](https://example.com).",
            "active": True,
            "language": "de",
        },
        format="json",
    )

    assert response.status_code == 201
    blog = Blog.objects.get(title="Markdown Blog")
    assert blog.markdown.startswith("## Einleitung")
    assert "<h2" in blog.body
    assert "<strong>fett</strong>" in blog.body
    assert blog.code[0]["name"] == "textArea"
    assert response.data["markdown"] == blog.markdown


def test_write_key_can_upload_blog_media_and_use_markdown(cms_user):
    _, raw_key = issue_key(cms_user)
    client = api_client_for(raw_key)

    upload_response = client.post(
        "/api/cms/blog/media/",
        {
            "file": image_upload(),
            "title": "Event Bild",
            "alt_text": "Volles Haus beim Event",
        },
        format="multipart",
    )

    assert upload_response.status_code == 201
    assert fileentry.objects.filter(title="Event Bild").exists()
    assert upload_response.data["markdown"].startswith("![Volles Haus beim Event](")
    assert upload_response.data["url"].endswith(".png")

    create_response = client.post(
        "/api/cms/blog/",
        {
            "title": "Blog mit Bild",
            "description": "Beschreibung mit Bild.",
            "markdown": f"## Galerie\n\n{upload_response.data['markdown']}",
            "active": True,
            "language": "de",
        },
        format="json",
    )

    assert create_response.status_code == 201
    blog = Blog.objects.get(title="Blog mit Bild")
    assert upload_response.data["markdown"] in blog.markdown
    assert 'class="rounded-2xl my-4"' in blog.body


def test_read_only_key_cannot_upload_blog_media(cms_user):
    _, raw_key = issue_key(cms_user, access_level=DeveloperApiKey.READ)
    client = api_client_for(raw_key)

    response = client.post(
        "/api/cms/blog/media/",
        {"file": image_upload()},
        format="multipart",
    )

    assert response.status_code == 403
    assert fileentry.objects.count() == 0


def test_cms_builder_create_stores_markdown(client, cms_user):
    client.force_login(cms_user)
    response = client.post(
        reverse("ycms:blog-create"),
        {
            "title": "Builder Markdown Blog",
            "description": "Builder Beschreibung.",
            "body": '<div><h2 class="text-2xl">Builder Titel</h2><p>Builder Text</p></div>',
            "code": '[{"name":"title-1","type":"h2","value":"Builder Titel"},{"name":"textArea","type":"p","value":"<p>Builder Text</p>"}]',
            "active": "true",
        },
    )

    assert response.status_code == 201
    blog = Blog.objects.get(title="Builder Markdown Blog")
    assert "## Builder Titel" in blog.markdown
    assert "Builder Text" in blog.markdown


def test_blog_detail_includes_language_variant_links(cms_user):
    root = Blog.objects.create(
        title="Deutscher Blog",
        description="Deutsche Beschreibung.",
        body="<p>Deutsch</p>",
        code=[],
        active=True,
        language="de",
        author=cms_user,
    )
    translation = Blog.objects.create(
        title="English Blog",
        description="English description.",
        body="<p>English</p>",
        code=[],
        active=False,
        language="en",
        original=root,
        slug="english-blog-en",
        author=cms_user,
    )
    _, raw_key = issue_key(cms_user)
    client = api_client_for(raw_key)

    response = client.get(f"/api/cms/blog/{root.id}/")

    assert response.status_code == 200
    translations = response.data["translations"]
    assert {item["language"] for item in translations} == {"de", "en"}
    assert translations[0]["is_original"] is True
    assert any(
        item["id"] == translation.id and item["api_url"].endswith(f"/api/cms/blog/{translation.id}/")
        for item in translations
    )


def test_creating_duplicate_language_variant_is_rejected(cms_user):
    root = Blog.objects.create(
        title="Original Blog",
        description="Original description.",
        body="<p>Deutsch</p>",
        code=[],
        active=True,
        language="de",
        author=cms_user,
    )
    Blog.objects.create(
        title="English Blog",
        description="English description.",
        body="<p>English</p>",
        code=[],
        active=False,
        language="en",
        original=root,
        slug="english-blog-en",
        author=cms_user,
    )
    _, raw_key = issue_key(cms_user)
    client = api_client_for(raw_key)

    response = client.post(
        "/api/cms/blog/",
        {
            "title": "Another English Blog",
            "description": "Another description.",
            "body": "<p>Duplicate</p>",
            "language": "en",
            "original": root.id,
        },
        format="json",
    )

    assert response.status_code == 400
    assert root.translations.filter(language="en").count() == 1


def test_expired_key_is_rejected(cms_user):
    _, raw_key = issue_key(
        cms_user,
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    client = api_client_for(raw_key)

    response = client.get("/api/cms/blog/")

    assert response.status_code == 401
