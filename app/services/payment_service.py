import base64
import hmac
import json
import random
import time
import hashlib

import requests

from app.services.package_service import PackageService
from app.services.user_service import UserService


class PaymentService:

    @staticmethod
    def get_token(app, payload, package_id, user_address, user_phone, user_ip):
        user_id = payload['sub']
        user = UserService.get_user_by_id(user_id)
        package = PackageService.get_package_by_id(package_id)
        country_code = PaymentService.get_country_code_by_ip(user_ip) or "TL"
        print(country_code)

        price = package["monthlyOriginalPrice"]
        #currency = 'USD'
        #if country_code == "TR":  # Eğer IP adresi Türkiye'ye aitse, fiyatı TL'ye çevir
        price = PaymentService.convert_to_tl(price)
        currency = 'TL'
        price = int(price * 100)
        print(f"price {price}")

        with app.app_context():
            merchant_id = app.config['MERCHANT_ID']
            merchant_key = app.config['MERCHANT_KEY']
            merchant_salt = app.config['MERCHANT_SALT']
            merchant_ok_url = app.config['MERCHANT_OK_URL']
            merchant_fail_url = app.config['MERCHANT_FAIL_URL']

        basket = base64.b64encode(json.dumps([[package["title"], str(price), 1],]).encode())
        user_ip = '104.28.216.174'
        timeout_limit = '30' # İşlem zaman aşımı süresi - dakika cinsinden
        debug_on = '1' # Hata mesajlarının ekrana basılması için entegrasyon ve test sürecinde 1 olarak bırakın. Daha sonra 0 yapabilirsiniz.
        test_mode = '1' # Mağaza canlı modda iken test işlem yapmak için 1 olarak gönderilebilir.
        no_installment = '0'  # Taksit yapılmasını istemiyorsanız, sadece tek çekim sunacaksanız 1 yapın
        max_installment = '0' # Sayfada görüntülenecek taksit adedini sınırlamak istiyorsanız uygun şekilde değiştirin. Sıfır (0) gönderilmesi durumunda yürürlükteki en fazla izin verilen taksit geçerli olur.
        merchant_oid = PaymentService.generate_merchant_oid()

        hash_str = merchant_id + user_ip + merchant_oid + user.email + str(price) + basket.decode() + no_installment + max_installment + currency + test_mode
        paytr_token = base64.b64encode(
            hmac.new(merchant_key.encode(), (hash_str + merchant_salt).encode(), hashlib.sha256).digest()
        )

        params = {
            'merchant_id': merchant_id,
            'user_ip': user_ip,
            'merchant_oid': merchant_oid,
            'email': user.email,
            'payment_amount': int(price),
            'paytr_token': paytr_token,
            'user_basket': basket,
            'debug_on': debug_on,
            'no_installment': no_installment,
            'max_installment': max_installment,
            'user_name': user.username,
            'user_address': user_address,
            'user_phone': user_phone,
            'merchant_ok_url': merchant_ok_url,
            'merchant_fail_url': merchant_fail_url,
            'timeout_limit': timeout_limit,
            'currency': currency,
            'test_mode': test_mode
        }

        try:
            result = requests.post('https://www.paytr.com/odeme/api/get-token', params, timeout=30)
            res = result.json()
            return res
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error occurred during the request: {str(e)}")

    @staticmethod
    def get_country_code_by_ip(ip_address):
        """Kullanıcının IP adresine göre ülke kodunu döndürür"""
        try:
            # IP geolocation servisi için örnek bir API kullanımı (free ip geolocation services kullanılabilir)
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            data = response.json()

            if response.status_code == 200 and "countryCode" in data:
                print("get country returnden döndü")
                return data["countryCode"]
            else:
                print("get country none döndü")
                return None
        except Exception as e:
            print(f"IP ülke kodu alınırken hata oluştu: {str(e)}")
            return None

    @staticmethod
    def convert_to_tl(price_in_usd):
        """Dolar cinsinden gelen fiyatı TL'ye çevirir"""
        try:
            # Döviz kuru API'sinden güncel dolar-TL kurunu al
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            data = response.json()

            if response.status_code == 200 and "rates" in data and "TRY" in data["rates"]:
                usd_to_try_rate = data["rates"]["TRY"]
                print("çevirme başarılı")
                return price_in_usd * usd_to_try_rate
            else:
                return price_in_usd  # Eğer kur alınamazsa, fiyatı dolarda bırak
        except Exception as e:
            print(f"Döviz kuru alınırken hata oluştu: {str(e)}")
            return price_in_usd
    @staticmethod
    def generate_merchant_oid():
        # Mevcut zamanı al ve milisaniyeye kadar formatla
        timestamp = int(time.time() * 1000)

        # Random 6 haneli bir sayı oluştur
        random_number = random.randint(100000, 999999)

        # İstediğiniz formatta merchant_oid oluştur
        merchant_oid = f"HORIAR{timestamp}{random_number}PAYTR"

        return merchant_oid