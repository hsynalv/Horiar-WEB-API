import logging

import requests

def send_welcome_email(to,username):
    payload = {
        "email": to,
        "type": "welcome",
        "data": {
            "name": username
        }
    }

    try:
        response = requests.post("http://3.68.189.144:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        logging.info("Email başarıyla gönderildi!", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Email gönderme hatası: {e}")

def send_purchase_email(to, username, title, credit_count, date, subject, first):
    payload = {
        "email": to,
        "type": "purchase",
        "data": {
            "username": username,
            "title": title,
            "credit_amount": credit_count,
            "date": date,
            "subject": subject,
            "first": first
        }
    }

    logging.info(payload)

    try:
        response = requests.post("http://3.68.189.144:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        logging.info("Email başarıyla gönderildi!", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Email gönderme hatası: {e}")


def send_password_reset_email(email, reset_link):
    """
    Kullanıcıya şifre sıfırlama e-postası gönderir.
    reset_link, kullanıcının şifresini sıfırlayabilmesi için gerekli bağlantıyı içerir.
    """
    # Username bilgisine erişiminiz yoksa, email'in "@" öncesi kısmını kullanıyoruz.
    username = email.split('@')[0]
    payload = {
        "email": email,
        "type": "resetPassword",
        "data": {
            "username": username,
            "reset_link": reset_link
        }
    }

    logging.info(f"payload: {payload}")

    try:
        response = requests.post("http://3.68.189.144:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        logging.info("Reset şifre email başarılı şekilde gönderildi!", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Reset şifre email gönderme hatası: {e}") 

def send_support_reset_email(authorized_email, email, username, message):
    """
    Kullanıcıya destek e-postası gönderir.
    """
    payload = {
        "email": authorized_email,
        "type": "support",
        "data": {
            "name": username,
            "message": message,
            "email": email
        }
    }

    logging.info(f"payload: {payload}")

    try:
        response = requests.post("http://3.68.189.144:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        logging.info("Support email başarılı şekilde gönderildi!", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Support email gönderme hatası: {e}") 