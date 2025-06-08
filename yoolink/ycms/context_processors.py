from .models import UserSettings

def user_settings_context(request):
    context = {}
    user_settings_qs = UserSettings.objects.filter(user__is_staff=False)
    if user_settings_qs.exists():
        context['owner_data'] = user_settings_qs.first()
    return context
