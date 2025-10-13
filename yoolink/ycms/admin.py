from django.contrib import admin
from .models import Button, Galerie, Notification, OpeningHours, PricingCard, PricingFeature, ShippingAddress, TeamMember, UserSettings, GaleryImage, FAQ, Product, VideoFile, fileentry, Blog, Message, TextContent, Order, OrderItem, Review, Brand, Category

# Register your models here.


admin.site.register(Galerie)
admin.site.register(GaleryImage)
admin.site.register(FAQ)
admin.site.register(fileentry)
admin.site.register(Blog)
admin.site.register(TextContent)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(UserSettings)
admin.site.register(OpeningHours)
admin.site.register(ShippingAddress)
admin.site.register(TeamMember)
admin.site.register(PricingFeature)
admin.site.register(Button)
admin.site.register(PricingCard)
admin.site.register(VideoFile)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'title', 'date', 'seen')
    search_fields = ('name', 'email', 'title', 'message')  # <- wichtig für autocomplete
    list_filter = ('seen', 'date')
    ordering = ('-date',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'seen', 'created_at', 'linked_object')
    list_filter = ('priority', 'seen', 'created_at')
    search_fields = (
        'title', 'description',
        'message__name', 'message__email', 'message__title',
        'order__buyer_email',
    )
    autocomplete_fields = ('message',)         # <- funktioniert jetzt, weil MessageAdmin search_fields hat
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_unread']

    def linked_object(self, obj):
        if obj.message_id:
            return f"Message #{obj.message_id}"
        if obj.link_url:
            return obj.link_url
        return '—'
    linked_object.short_description = 'Verknüpft mit'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(seen=True)
        self.message_user(request, f"{updated} Benachrichtigung(en) als gelesen markiert.")
    mark_as_read.short_description = "Ausgewählte als gelesen markieren"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(seen=False)
        self.message_user(request, f"{updated} Benachrichtigung(en) als ungelesen markiert.")
    mark_as_unread.short_description = "Ausgewählte als ungelesen markieren"
