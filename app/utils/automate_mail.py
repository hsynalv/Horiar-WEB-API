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
        response = requests.post("http://localhost:3000/send-email", json=payload)
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
        response = requests.post("http://localhost:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        logging.info("Email başarıyla gönderildi!", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Email gönderme hatası: {e}")