"""Site-wide SEO structured data (JSON-LD).

Builds the Organization + WebSite + LocalBusiness ``@graph`` that is rendered on
every public page (see ``base.html``). Scalar NAP values (name, e-mail, phone,
street, logo) are pulled from the CMS site-owner record (``UserSettings``) so they
stay editable in the CMS, with safe fallbacks so the markup is never empty/broken.

This module deliberately has no Django imports so it can be unit-tested in
isolation: it only reads attributes off the passed-in ``owner`` object.
"""

import json

SITE_BASE_URL = "https://yoolink.de"

# Static fallbacks (legally correct NAP per the Impressum) used when the CMS
# field is empty. Postal code / city / region live here because the CMS only
# stores a single free-text address field today.
_FALLBACK_NAME = "YooLink"
_FALLBACK_EMAIL = "info@yoolink.de"
_FALLBACK_PHONE = "+49 170 5977862"
_FALLBACK_STREET = "Am Altbach 6"
_POSTAL_CODE = "94491"
_LOCALITY = "Hengersberg"
_REGION = "Bayern"
_COUNTRY = "DE"
_GEO_LAT = 48.7667  # Hengersberg (registered business location)
_GEO_LNG = 13.0500
_OWNER_PERSON = "Sebastian Rauch"

# Service areas (SEO targeting, not part of the legal NAP).
_AREA_SERVED = [
    {"@type": "City", "name": "Passau"},
    {"@type": "City", "name": "Regensburg"},
    {"@type": "City", "name": "Deggendorf"},
    {"@type": "AdministrativeArea", "name": "Niederbayern"},
]

_SAME_AS = [
    "https://www.instagram.com/yoolinkde/",
    "https://x.com/YooLinkDE",
]


def _field(owner, attr, fallback):
    """Return a stripped CMS string field, or the fallback when empty/missing."""
    value = getattr(owner, attr, "") if owner else ""
    if isinstance(value, str):
        value = value.strip()
    return value or fallback


def _logo_url(owner):
    """Absolute logo URL: CMS-uploaded logo if present, else the static OG image."""
    url = ""
    try:
        if owner and getattr(owner, "logo", None):
            url = owner.logo.url or ""
    except Exception:
        url = ""
    if not url:
        return f"{SITE_BASE_URL}/static/images/og-preview.png"
    if url.startswith("/"):
        return f"{SITE_BASE_URL}{url}"
    return url


def build_site_schema_jsonld(owner):
    """Build the site-wide JSON-LD string, safe to embed inside a <script> tag."""
    name = _field(owner, "company_name", _FALLBACK_NAME)
    email = _field(owner, "email", _FALLBACK_EMAIL)
    telephone = _field(owner, "tel_number", "") or _field(
        owner, "mobile_number", _FALLBACK_PHONE
    )
    street = _field(owner, "address", _FALLBACK_STREET)
    logo_url = _logo_url(owner)
    org_id = f"{SITE_BASE_URL}/#organization"

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": org_id,
                "name": name,
                "legalName": f"YooLink – Inhaber {_OWNER_PERSON}",
                "url": f"{SITE_BASE_URL}/",
                "email": email,
                "telephone": telephone,
                "founder": {"@type": "Person", "name": _OWNER_PERSON},
                "logo": {"@type": "ImageObject", "url": logo_url},
                "image": logo_url,
                "sameAs": list(_SAME_AS),
            },
            {
                "@type": "WebSite",
                "@id": f"{SITE_BASE_URL}/#website",
                "url": f"{SITE_BASE_URL}/",
                "name": name,
                "description": "Webdesign Agentur im Raum Niederbayern",
                "publisher": {"@id": org_id},
                "inLanguage": "de-DE",
            },
            {
                "@type": ["ProfessionalService", "LocalBusiness"],
                "@id": f"{SITE_BASE_URL}/#localbusiness",
                "name": name,
                "url": f"{SITE_BASE_URL}/",
                "image": logo_url,
                "email": email,
                "telephone": telephone,
                "priceRange": "ab 40 €/Monat",
                "parentOrganization": {"@id": org_id},
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": street,
                    "postalCode": _POSTAL_CODE,
                    "addressLocality": _LOCALITY,
                    "addressRegion": _REGION,
                    "addressCountry": _COUNTRY,
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": _GEO_LAT,
                    "longitude": _GEO_LNG,
                },
                "areaServed": list(_AREA_SERVED),
            },
        ],
    }

    payload = json.dumps(graph, ensure_ascii=False)
    # Neutralise characters that could break out of the surrounding <script>.
    return (
        payload.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
