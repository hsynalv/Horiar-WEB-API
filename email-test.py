import requests

def send_test_email():
    payload = {
        "email": "hhsynalv@gmail.com",
        "type": "purchase",
        "data": {
            "username": "user123",
            "title": "Kredi Tanımlaması Gerçekleşti",
            "username": "credit_amount",
            "date": "user123",
            "subject": "Kredi Tanımlamanız Gerçekleşti"
        }
    }

    try:
        response = requests.post("http://localhost:3000/send-email", json=payload)
        response.raise_for_status()  # Hata durumunda istisna fırlatır
        print("Email başarıyla gönderildi!", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Email gönderme hatası: {e}")

if __name__ == "__main__":
    send_test_email()