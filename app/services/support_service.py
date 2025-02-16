import logging

from app.utils.automate_mail import send_support_reset_email

support_logger = logging.getLogger("support")

def log_support_request(name, message, payload):
    """
    Kullanıcının destek talebini log dosyasına kaydeder.
    """
    email = payload['email']
    authorized_emails = ["halav@horiar.com", "anilkoroglu@horiar.com"]


    # Log kaydı oluştur
    log_message = f"Name: {name} | E-mail: {email} | Message: {message}"
    support_logger.info(log_message)

    for authorized_email in authorized_emails:
        send_support_reset_email(authorized_email, email, name, message)
