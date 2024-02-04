from yoolink.ycms.models import UserSettings, Order
from django.core.mail import send_mail
from django.conf import settings

def send_payment_confirmation(order: Order):
    buyer_email = order.buyer_email
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()
    subject = f"Ihr Auftrag {order.id} wurde bezahlt"
    message = f"Vielen Dank! Ihr Auftrag mit der Auftragsnummer {order.id} wurde erfolgreich bezahlt. Die Produkte werden in Kürze an Sie versandt.\n\nDetails Ihres Auftrags:\n"
    
    for item in order.items.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"

    message += f"\nGesamtpreis: {order.total():.2f} Euro\n"
    message += f"\nVersandadresse:\n{order.buyer_address}\n"
    message += f"\nVielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )

    # Send confirmation email to admin
    admin_message = f"Der Auftrag {order.id} wurde bezahlt und sollte nun versandt werden. Details unter: {settings.DASHBOARD_URL}cms/orders/{order.id}/"
    send_mail(
        f"Auftrag {order.id} wurde bezahlt",
        admin_message,
        settings.EMAIL_HOST_USER,
        [user_settings.email],
        fail_silently=False,
    )

def send_ready_for_pickup_confirmation(order: Order):
    buyer_email = order.buyer_email
    user_settings = UserSettings.objects.filter(user__is_staff=True).first()
    subject = f"Ihr Auftrag {order.id} ist bereit zur Abholung"
    message = f"Ihr Auftrag mit der Auftragsnummer {order.id} ist bereit zur Abholung. Die Produkte können während der Öffnungszeiten abgeholt und bezahlt werden.\n\nDetails Ihres Auftrags:\n"
    
    for item in order.items.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"

    message += f"\nGesamtpreis: {order.total():.2f} Euro\n"
    message += f"\nVielen Dank für Ihre Reservierung und bis bald!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )

    # Send confirmation email to admin
    admin_message = f"Der Auftrag {order.id} ist bereit zur Abholung. Details unter: {settings.DASHBOARD_URL}cms/orders/{order.id}/"
    send_mail(
        f"Auftrag {order.id} ist bereit zur Abholung",
        admin_message,
        settings.EMAIL_HOST_USER,
        [user_settings.email],
        fail_silently=False,
    )

def send_shipping_confirmation(order : Order, user_settings: UserSettings):
    buyer_email = order.buyer_email
    # Check if the request.user is a staff member
    
    subject = f"Ihre Produkte sind auf dem Weg"
    message = f"Ihre Produkte aus dem Auftrag {order.id} sind auf dem Weg zu Ihnen. Vielen Dank für Ihren Einkauf!\n\nDetails Ihres Auftrags:\n"
    
    for item in order.items.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"

    message += f"\nGesamtpreis: {order.total():.2f} Euro\n"
    message += f"\nVersandadresse:\n{order.buyer_address}\n"
    message += f"\nWir informieren Sie, wenn die Produkte unterwegs sind. Vielen Dank!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )