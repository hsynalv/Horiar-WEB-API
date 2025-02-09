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
        logging.ERROR(f"Email gönderme hatası: {e}")