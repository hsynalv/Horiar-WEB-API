import logging

support_logger = logging.getLogger("support")

def log_support_request(name, message, payload):
    """
    Kullanıcının destek talebini log dosyasına kaydeder.
    """
    email = payload['email']


    # Log kaydı oluştur
    log_message = f"Name: {name} | E-mail: {email} | Message: {message}"
    support_logger.info(log_message)
