from yoolink.ycms.models import UserSettings, Order
from django.core.mail import send_mail
from django.conf import settings

def send_payment_confirmation(order: Order):
    buyer_email = order.buyer_email
    user_settings = UserSettings.objects.filter(user__is_staff=False).first()
    phone_number = user_settings.tel_number
    email = user_settings.email
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website
    subject = f"Ihr Auftrag {order.id} wurde bezahlt"
    message = f"Vielen Dank! Ihr Auftrag mit der Auftragsnummer #{order.id} wurde erfolgreich bezahlt."
    if order.shipping == "SHIPPING":
        message += f"\nDie Produkte werden in Kürze an Sie versandt. \nSie erhalten eine weitere Email, sobald die Ware verschickt wird."
    elif order.shipping == "PICKUP":
        message += f"\nDie Produkte werden bereitgestellt. Sie erhalten in Kürze eine Email, sobald Sie die Ware abholen können"

    message += "\n\nDetails Ihres Auftrags:\n"
    for item in order.orderitem_set.all():
        message += f"{item.quantity}x {item.product.title} - {item.subtotal():.2f} Euro\n"

    message += f"------------------------------------------"
    message += f"\nNettopreis: {order.total_with_tax():.2f} Euro"
    message += f"\nLieferung: {order.shipping_price():.2f} Euro"
    message += f"\nUmsatzsteuer (19%): {order.calculate_tax():.2f} Euro"
    message += f"\n------------------------------------------"
    message += f"\nGesamtpreis (mit 19% Steuern): {order.total():.2f} Euro\n\n"
    message += f"Ihre ausgewählte Liefermethode: {order.get_shipping_display()}"
    if order.shipping == "SHIPPING":
        message += f"\nVersandadresse: {order.buyer_address.get_shipping_address()}\n"
    elif order.shipping == "PICKUP":
        message += f"\nRechnungsadresse: {order.buyer_address.get_shipping_address()}\n"
    message += f"\nIhre ausgewählte Bezahlmethode: {order.get_payment_display()}"

    message += f"\nVielen Dank für Ihr Vertrauen!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    if phone_number and phone_number != "0":
        message += f"\nTel. {phone_number}"

    if fax_number and fax_number != "0":
        message += f"\nFax {fax_number}"

    if mobile_number and mobile_number != "0":
        message += f"\nHandy {mobile_number}"
    if email:
        message += f"\n{email}"
    if website:
        message += f"\n{website}"
    message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )

    # Send confirmation email to admin
    """admin_message = f"Der Auftrag {order.id} wurde bezahlt und sollte nun versandt werden. Details unter: {settings.DASHBOARD_URL}cms/orders/{order.id}/"
    send_mail(
        f"Auftrag {order.id} wurde bezahlt",
        admin_message,
        settings.EMAIL_HOST_USER,
        [user_settings.email],
        fail_silently=False,
    )"""

def send_ready_for_pickup_confirmation(order: Order):
    buyer_email = order.buyer_email
    user_settings = UserSettings.objects.filter(user__is_staff=False).first()
    phone_number = user_settings.tel_number
    email = user_settings.email
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website
    subject = f"Ihr Auftrag {order.id} ist bereit zur Abholung"
    message = f"Ihr Auftrag mit der Auftragsnummer #{order.id} ist bereit zur Abholung. \nDie Produkte können während der Öffnungszeiten abgeholt werden."
    message += f"\nVielen Dank für Ihre Bestellung und bis bald!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    if phone_number and phone_number != "0":
        message += f"\nTel. {phone_number}"

    if fax_number and fax_number != "0":
        message += f"\nFax {fax_number}"

    if mobile_number and mobile_number != "0":
        message += f"\nHandy {mobile_number}"
    if email:
        message += f"\n{email}"
    if website:
        message += f"\n{website}"
    message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )

    # Send confirmation email to admin
    """admin_message = f"Der Auftrag {order.id} ist bereit zur Abholung. Details unter: {settings.DASHBOARD_URL}cms/orders/{order.id}/"
    send_mail(
        f"Auftrag {order.id} ist bereit zur Abholung",
        admin_message,
        settings.EMAIL_HOST_USER,
        [user_settings.email],
        fail_silently=False,
    )"""

def send_shipping_confirmation(order : Order):
    buyer_email = order.buyer_email
    # Check if the request.user is a staff member
    user_settings = UserSettings.objects.filter(user__is_staff=False).first()
    phone_number = user_settings.tel_number
    email = user_settings.email
    fax_number = user_settings.fax_number
    mobile_number = user_settings.mobile_number
    website = user_settings.website
    subject = f"Ihre Produkte sind auf dem Weg"
    message = f"Ihre Produkte aus dem Auftrag #{order.id} sind auf dem Weg zu Ihnen. \nVielen Dank für Ihren Einkauf!\n\nDetails Ihres Auftrags:\n"
    
    message += f"\nVersandadresse: {order.buyer_address.get_shipping_address()}\n"
    message += f"\nWir informieren Sie, wenn die Produkte unterwegs sind. Vielen Dank!\n\nMit freundlichen Grüßen,\n{user_settings.full_name}"

    if phone_number and phone_number != "0":
        message += f"\nTel. {phone_number}"

    if fax_number and fax_number != "0":
        message += f"\nFax {fax_number}"

    if mobile_number and mobile_number != "0":
        message += f"\nHandy {mobile_number}"
    if email:
        message += f"\n{email}"
    if website:
        message += f"\n{website}"
    message += "\n\nUnterstützt durch YooLink\nhttps://yoolink.de"

    # Send confirmation email to buyer
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [buyer_email],
        fail_silently=False,
    )