from yoolink.ycms.views import get_active_language
from .models import Notification, UserSettings

def user_settings_context(request):
    context = {}
    user_settings_qs = UserSettings.objects.filter(user__is_staff=False)
    if user_settings_qs.exists():
        context['owner_data'] = user_settings_qs.first()
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