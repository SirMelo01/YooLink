from django.contrib import admin

from .models import (
    FAQ,
    Blog,
    Button,
    CMSRole,
    CMSUserRole,
    DeveloperApiKey,
    GaleryImage,
    Galerie,
    Message,
    OpeningHours,
    PricingCard,
    PricingFeature,
    TeamMember,
    UserSettings,
    VideoFile,
    WebsiteSettings,
    fileentry,
)


admin.site.register(Galerie)
admin.site.register(GaleryImage)
admin.site.register(FAQ)
admin.site.register(fileentry)
admin.site.register(Blog)
admin.site.register(UserSettings)
admin.site.register(WebsiteSettings)
admin.site.register(CMSRole)
admin.site.register(CMSUserRole)
admin.site.register(OpeningHours)
admin.site.register(TeamMember)
admin.site.register(PricingFeature)
admin.site.register(Button)
admin.site.register(PricingCard)
admin.site.register(VideoFile)


@admin.register(DeveloperApiKey)
class DeveloperApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prefix",
        "created_by",
        "access_level",
        "allowed_apps",
        "expires_at",
        "revoked_at",
        "last_used_at",
    )
    list_filter = ("access_level", "revoked_at", "expires_at")
    search_fields = ("name", "prefix", "created_by__username", "created_by__email")
    readonly_fields = ("prefix", "key_hash", "created_at", "updated_at", "last_used_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "title", "date", "seen")
    search_fields = ("name", "email", "title", "message")
    list_filter = ("seen", "date")
    ordering = ("-date",)
