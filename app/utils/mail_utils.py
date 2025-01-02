from flask_mail import Message
from app.extensions.mail import mail  # Doğru mail objesini import ettik
import logging

# Logger yapılandırması
logger = logging.getLogger(__name__)

def send_email(subject, recipients, body, html_body=None):
    msg = Message(
        subject,
        recipients=recipients,
        body=body,
        html=html_body
    )
    try:
        mail.send(msg)
        logger.info(f"Email sent successfully to {recipients}")
    except Exception as e:
        error_message = f"Failed to send email to {recipients}. Error: {str(e)}"
        logger.error(error_message)
        send_error_email("Email Send Error", error_message)


def send_error_email(subject, error_details):
    msg = Message(
        subject=subject,
        recipients=["hhsynalv@gmail.com"],  # Hata e-postalarını alacak admin e-posta adresleri
        body=error_details
    )
    try:
        mail.send(msg)
        logger.info("Error email sent successfully.")
    except Exception as e:
        logger.critical(f"Failed to send error email. Error: {str(e)}")
        # print kullanımı loglarla değiştirilmiştir.

