import json
from datetime import time

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from yoolink.users.tests.factories import UserFactory
from yoolink.ycms.models import (
    FAQ,
    AnyFile,
    Button,
    Galerie,
    Message,
    Notification,
    OpeningHours,
    PricingCard,
    PricingFeature,
    TeamMember,
    TextContent,
    UserSettings,
    VideoFile,
    fileentry,
)
from yoolink.ycms.spam_detection import is_spam_message, score_text_for_spam

pytestmark = pytest.mark.django_db


@pytest.fixture
def cms_user():
    user = UserFactory(email="owner@example.com")
    user.set_password("password12345")
    user.save(update_fields=["password", "email"])
    UserSettings.objects.create(
        user=user,
        email=user.email,
        full_name="Owner User",
        company_name="YooLink Test",
    )
    return user


@pytest.fixture
def logged_in_client(cms_user):
    from django.test import Client

    client = Client()
    client.force_login(cms_user)
    return client


def _json_post(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def test_cms_dashboard_requires_login_and_shows_module_counts(client, logged_in_client):
    anonymous_response = client.get(reverse("ycms:cms"))
    assert anonymous_response.status_code == 302

    FAQ.objects.create(question="Question", answer="Answer")
    Button.objects.create(text="Kontakt", url="https://example.com")
    Galerie.objects.create(title="Hero")

    response = logged_in_client.get(reverse("ycms:cms"))

    assert response.status_code == 200
    assert b"YooLink CMS" in response.content
    assert response.context["button_count"] == 1
    assert response.context["galery_count"] == 1


def test_faq_create_update_reorder_and_delete(logged_in_client):
    create_response = logged_in_client.get(
        reverse("ycms:faq-update"),
        {"question": "Wie schnell?", "answer": "Sehr schnell."},
    )
    assert create_response.status_code == 200
    faq_id = create_response.json()["id"]

    update_response = logged_in_client.post(
        reverse("ycms:faq-update"),
        {"faq_id": faq_id, "question": "Wie sicher?", "answer": "Mit Tests."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["success"] is True

    FAQ.objects.create(question="Zweite Frage", answer="Zweite Antwort")
    order_payload = [
        {"id": obj.id, "question": obj.question, "answer": obj.answer}
        for obj in FAQ.objects.order_by("-id")
    ]
    reorder_response = logged_in_client.post(
        reverse("ycms:faq-sort"),
        {"faqs": json.dumps(order_payload)},
    )
    assert reorder_response.status_code == 200
    assert list(FAQ.objects.order_by("order").values_list("id", flat=True)) == [
        item["id"] for item in order_payload
    ]

    delete_response = logged_in_client.post(reverse("ycms:faq-update", args=[faq_id]))
    assert delete_response.status_code == 200
    assert not FAQ.objects.filter(id=faq_id).exists()


def test_text_content_save_assigns_media_and_gallery_slots(logged_in_client):
    image = fileentry.objects.create(
        file=SimpleUploadedFile("hero.jpg", b"image", content_type="image/jpeg")
    )
    gallery = Galerie.objects.create(title="Hero gallery")
    video = VideoFile.objects.create(
        file=SimpleUploadedFile("hero.mp4", b"video", content_type="video/mp4"),
        title="Hero video",
    )

    response = logged_in_client.post(
        reverse("ycms:save_text_content"),
        {
            "name": "main_hero",
            "header": "Header",
            "title": "Title",
            "description": "Description",
            "buttonText": "Start",
            "customText": "[]",
            "images": json.dumps([{"id": image.id, "key": "main_hero_image"}]),
            "galerien": json.dumps([{"id": gallery.id, "key": "main_hero"}]),
            "videos": json.dumps([{"id": video.id, "key": "main_hero_video"}]),
        },
    )

    assert response.status_code == 200
    content = TextContent.objects.get(name="main_hero")
    assert content.title == "Title" or getattr(content, "title_de", "") == "Title"
    image.refresh_from_db()
    gallery.refresh_from_db()
    video.refresh_from_db()
    assert image.place == "main_hero_image"
    assert gallery.place == "main_hero"
    assert video.place == "main_hero_video"


def test_profile_update_resets_2fa_when_email_changes(logged_in_client, cms_user):
    settings_obj = cms_user.usersettings
    settings_obj.two_factor_email_enabled = True
    settings_obj.two_factor_email_verified = True
    settings_obj.two_factor_email_code = "123456"
    settings_obj.two_factor_email_code_expires_at = timezone.now()
    settings_obj.save()

    response = logged_in_client.post(
        reverse("ycms:settings-update"),
        {
            "email": "new-owner@example.com",
            "full_name": "New Owner",
            "company_name": "New Company",
            "tel_number": "123",
            "fax_number": "",
            "mobile_number": "",
            "website": "https://example.com",
            "address": "Main Street",
            "global_font": "font-serif",
        },
    )

    assert response.status_code == 200
    settings_obj.refresh_from_db()
    cms_user.refresh_from_db()
    assert settings_obj.email == "new-owner@example.com"
    assert cms_user.email == "new-owner@example.com"
    assert settings_obj.two_factor_email_enabled is False
    assert settings_obj.two_factor_email_code == ""


def test_opening_hours_update_and_vacation_window(logged_in_client, cms_user):
    OpeningHours.objects.create(user=cms_user, day="MON")

    response = logged_in_client.post(
        reverse("ycms:openinghours-update"),
        {
            "opening_hours": json.dumps(
                [
                    {
                        "day": "MON",
                        "isOpen": True,
                        "startTime": "08:00",
                        "endTime": "17:00",
                        "hasLunchBreak": True,
                        "lunchBreakStart": "12:00",
                        "lunchBreakEnd": "13:00",
                    }
                ]
            ),
            "vacation": "true",
            "vacationText": "Wir sind kurz weg.",
            "vacation_start": "2026-05-01T08:00",
            "vacation_end": "2026-05-10T18:00",
        },
    )

    assert response.status_code == 200
    opening = OpeningHours.objects.get(user=cms_user, day="MON")
    assert opening.calculate_opening_periods() == [
        (time(8, 0), time(12, 0)),
        (time(13, 0), time(17, 0)),
    ]
    cms_user.usersettings.refresh_from_db()
    assert cms_user.usersettings.vacation is True


def test_opening_hours_view_creates_missing_user_settings(client):
    user = UserFactory(email="missing-settings@example.com")
    client.force_login(user)

    response = client.get(reverse("ycms:openinghours-view"))

    assert response.status_code == 200
    assert UserSettings.objects.filter(user=user, email=user.email).exists()
    assert OpeningHours.objects.filter(user=user).count() == len(OpeningHours.DAY_CHOICES)


def test_team_button_and_pricing_management(logged_in_client):
    member_response = logged_in_client.post(
        reverse("ycms:create-team-member"),
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "position": "Developer",
            "years_with_team": "3",
            "active": "true",
        },
    )
    assert member_response.status_code == 200
    member = TeamMember.objects.get()
    assert member.display_order == 1

    button_response = _json_post(
        logged_in_client,
        reverse("ycms:button-create"),
        {"text": "Kontakt", "url": "https://example.com", "target": "_blank"},
    )
    assert button_response.status_code == 200
    button = Button.objects.get()

    pricing_response = _json_post(
        logged_in_client,
        reverse("ycms:pricingcard-create"),
        {
            "title": "Starter",
            "monthly_price": "25 EUR",
            "one_time_price": "250 EUR",
            "description": "Basis",
            "button_id": button.id,
            "active": True,
        },
    )
    assert pricing_response.status_code == 200
    card = PricingCard.objects.get()
    assert card.button == button

    features_response = _json_post(
        logged_in_client,
        reverse("ycms:pricingcard-features", args=[card.id]),
        {"features": [{"text": "Hosting"}, {"text": "Support"}]},
    )
    assert features_response.status_code == 200
    assert [feature.text for feature in PricingFeature.objects.order_by("order")] == [
        "Hosting",
        "Support",
    ]


def test_file_and_video_metadata_endpoints(logged_in_client):
    upload_response = logged_in_client.post(
        reverse("ycms:anyfile-upload"),
        {"file": SimpleUploadedFile("info.pdf", b"pdf", content_type="application/pdf")},
    )
    assert upload_response.status_code == 200
    any_file = AnyFile.objects.get()

    update_response = logged_in_client.post(
        reverse("ycms:anyfile-update", args=[any_file.id]),
        {"title": "Info", "description": "Download"},
    )
    assert update_response.status_code == 200

    video_response = logged_in_client.post(
        reverse("ycms:create_video"),
        {
            "file": SimpleUploadedFile("demo.mp4", b"video", content_type="video/mp4"),
            "title": "Demo",
            "description": "Video",
            "is_public": "true",
            "show_controls": "true",
        },
    )
    assert video_response.status_code == 200
    assert VideoFile.objects.get().slug == "demo"


def test_message_signal_creates_notifications_and_spam_flag():
    clean_message = Message.objects.create(
        name="Max",
        email="max@example.com",
        title="Projekt",
        message="Ich brauche eine neue Website.",
    )
    spam_message = Message.objects.create(
        name="Spam",
        email="casino@example.ru",
        title="Free spins",
        message="Claim now bonus https://example.com",
    )

    clean_notification = Notification.objects.get(message=clean_message)
    spam_notification = Notification.objects.get(message=spam_message)

    assert clean_notification.is_spam is False
    assert spam_notification.is_spam is True
    assert score_text_for_spam("FREE BONUS https://example.com") >= 4
    assert is_spam_message(spam_message) is True
