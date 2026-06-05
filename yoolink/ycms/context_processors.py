from yoolink.ycms.views import get_active_language
from yoolink.ycms.applications.notifications.models import Notification
from .models import UserSettings
from .seo_schema import build_site_schema_jsonld

def user_settings_context(request):
    context = {}
    owner_data = UserSettings.get_site_owner()
    if owner_data:
        context['owner_data'] = owner_data
    # Site-wide Organization/WebSite/LocalBusiness JSON-LD, built from the CMS
    # owner record (with safe fallbacks). Rendered once in base.html.
    try:
        context['site_schema_jsonld'] = build_site_schema_jsonld(owner_data)
    except Exception:
        context['site_schema_jsonld'] = ""
    return context

def notifications_context(request):
    unread_qs = Notification.objects.unread().latest_first()
    unread_count = unread_qs.count()

    limit = 8
    latest_unread = list(unread_qs[:limit])
    overflow = max(unread_count - limit, 0)

    return {
        'nav_unread_notifications_count': unread_count,        # Zahl fürs Badge
        'nav_latest_unread_notifications': latest_unread,      # Dropdown-Liste (nur ungelesen)
        'nav_unread_overflow': overflow,                       # „…und X weitere“
        'nav_unread_limit': limit,
    }

def cms_language_context(request):
    if not request.path.startswith('/cms/'):
        return {}
    
    return {
        "cms_language": get_active_language(request)
    }
