from flask_mail import Message
from app.extensions.mail import mail  # Doğru mail objesini import ettik

def send_email(subject, recipients, body, html_body=None):
    msg = Message(
        subject,
        recipients=recipients,
        body=body,
        html=html_body
    )
    mail.send(msg)


def send_error_email(subject, error_details):
    # E-posta içeriği
    msg = Message(
        subject=subject,
        recipients=["hhsynalv@gmail.com"],  # Hata e-postalarını alacak admin e-posta adresleri
        body=error_details
    )
    mail.send(msg)
    print("mail gönderildi")
