import base64
import hmac
import json
import logging
import os
import random
import time
import hashlib
from datetime import timedelta, datetime

import requests
from flask import current_app

from app.models.provision_model import Provision
from app.models.purchase_model import Purchase
from app.models.subscription_model import Subscription
from app.services.coupon_service import CouponService
from app.services.package_service import PackageService
from app.services.provision_service import ProvisionService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService


class PaymentService:

    # Özel logger'ı alıyoruz
    paytr_logger = logging.getLogger("paytr")

    @staticmethod
    def get_token(app, payload, package_id, user_address, user_phone, user_ip, is_annual, name_surname, coupon_name):
        user_id = payload['sub']
        user = UserService.get_user_by_id(user_id)
        package = PackageService.get_package_by_id(package_id)
        country_code = PaymentService.get_country_code_by_ip(user_ip) or "TL"

        if is_annual:
            price = package.get("yearlySalePrice") or package["yearlyOriginalPrice"]
        else:
            price = package.get("monthlySalePrice") or package["monthlyOriginalPrice"]

        currency = 'USD'
        if country_code == "TR":  # Eğer IP adresi Türkiye'ye aitse, fiyatı TL'ye çevir
            price = PaymentService.convert_to_tl(price)
            currency = 'TL'

        # KDV oranını belirliyoruz (örneğin %20 KDV)
        kdv_rate = 20

        # KDV'yi kupon uygulanmadan önceki fiyattan hesaplıyoruz
        #kdv_amount = (price * kdv_rate) / 100
        #PaymentService.paytr_logger.info(f"KDV applied: {kdv_amount}")

        # İndirim varsa kuponu al ve uygula
        if coupon_name:
            # Kuponu al
            coupon = CouponService.check_coupon(coupon_name, payload)

            if not coupon:
                raise ValueError("Invalid coupon code")  # Kupon bulunamazsa hata fırlatıyoruz

            # CouponService.use_coupon(coupon_name, user_id)

            # Kuponun indirim oranını alıyoruz
            discount_rate = coupon.get("discount_percentage") or 0

            # İndirimi fiyat üzerinden uyguluyoruz
            discount_amount = (price * discount_rate) / 100
            price -= discount_amount  # İndirimi fiyat üzerinden düşüyoruz

            PaymentService.paytr_logger.info(f"Discount applied: {discount_amount}, New price: {price}")

        # KDV'yi indirimsiz fiyat üzerinden ekliyoruz
        #price += kdv_amount  # KDV ekleniyor
        #PaymentService.paytr_logger.info(f"Price after KDV: {price}")

        price = int(price * 100)
        PaymentService.paytr_logger.info(f"gönderilmeden önce price: {price}")

        with app.app_context():
            merchant_id = app.config['MERCHANT_ID']
            merchant_key = app.config['MERCHANT_KEY']
            merchant_salt = app.config['MERCHANT_SALT']
            merchant_ok_url = app.config['MERCHANT_OK_URL']
            merchant_fail_url = app.config['MERCHANT_FAIL_URL']

        basket = base64.b64encode(json.dumps([[package["title"], str(price), 1],]).encode())
        timeout_limit = '30' # İşlem zaman aşımı süresi - dakika cinsinden
        debug_on = '0' # Hata mesajlarının ekrana basılması için entegrasyon ve test sürecinde 1 olarak bırakın. Daha sonra 0 yapabilirsiniz.
        test_mode = '1' # Mağaza canlı modda iken test işlem yapmak için 1 olarak gönderilebilir.
        no_installment = '0'  # Taksit yapılmasını istemiyorsanız, sadece tek çekim sunacaksanız 1 yapın
        max_installment = '1' # Sayfada görüntülenecek taksit adedini sınırlamak istiyorsanız uygun şekilde değiştirin. Sıfır (0) gönderilmesi durumunda yürürlükteki en fazla izin verilen taksit geçerli olur.
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
            'user_name': name_surname,
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

            # Yanıttaki "status" alanını kontrol et
            if res.get("status") == "success":
                if coupon_name:
                    resultForSave = PaymentService.save_provision(merchant_oid=merchant_oid, user_id=user_id, username=user.username,
                                                                  package_id=package_id, is_annual=is_annual, email=user.email, coupon_name=coupon["name"], amount=price)
                else:
                    resultForSave = PaymentService.save_provision(merchant_oid=merchant_oid, user_id=user_id, username=user.username,
                                                                  package_id=package_id, is_annual=is_annual, email=user.email, coupon_name=None)


                if resultForSave:
                    return res  # Başarılıysa yanıtı döndür
                else:
                    PaymentService.paytr_logger.error(f"Provizyon veritabanına kaydedilemedi. user: {user.username}")
                    raise Exception(f"Payment request failed: Provizyon veritabanına kaydedilemedi")
            else:
                # Başarısız durumda hata mesajı döndür
                error_message = res.get("reason", "Unknown error occurred")
                raise Exception(f"Payment request failed: {error_message}")

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
            PaymentService.paytr_logger.error(f"IP ülke kodu alınırken hata oluştu: {str(e)}")
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
            PaymentService.paytr_logger.error(f"Döviz kuru alınırken hata oluştu: {str(e)}")
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
    @staticmethod
    def save_provision(merchant_oid, user_id, username, package_id, is_annual, email, coupon_name,amount):
        """
        Verilen bilgileri kullanarak provizyon kaydı oluşturur ve veritabanına kaydeder.
        """
        try:
            # Yeni bir Provizyon nesnesi oluştur
            provision = Provision(
                merchant_oid=merchant_oid,
                user_id=user_id,  # ReferenceField'e uygun şekilde user_id ve package_id
                username=username,
                package_id=package_id,
                is_annual=is_annual,
                email=email,
                used_coupon=coupon_name,
                amount=amount
            )

            # Veritabanına kaydet
            provision.save()
            return True
        except Exception as e:
            PaymentService.paytr_logger.error(str(e))
            return False

    @staticmethod
    def callback_ok_funciton(app, request):
        with app.app_context():
            merchant_key = app.config['MERCHANT_KEY']
            merchant_salt = app.config['MERCHANT_SALT']

        # POST değerleri ile hash oluştur.
        hash_str = request['merchant_oid'] + merchant_salt + request['status'] + request['total_amount']
        hash = base64.b64encode(hmac.new(merchant_key.encode(), hash_str.encode(), hashlib.sha256).digest()).decode()

        # Oluşturulan hash'i, paytr'dan gelen post içindeki hash ile karşılaştır
        if hash != request['hash']:
            PaymentService.paytr_logger.info(f"hash geçersiz {hash} : {request['hash']}")
            return False

        # Siparişin durumunu kontrol et
        merchant_oid = request['merchant_oid']
        status = request['status']

        # Burada siparişi veritabanından sorgulayıp onaylayabilir veya iptal edebilirsiniz.
        if status == 'success':  # Ödeme Onaylandı
            PaymentService.paytr_logger.info(f"Order {merchant_oid} has been approved.")

            result = PaymentService.success_payment(merchant_oid)
            if result:
                return True
            else:
                return False
            # Müşteriye bildirim yapabilirsiniz (SMS, e-posta vb.)
            # Güncel tutarı post['total_amount'] değerinden alın.

        else:  # Ödemeye Onay Verilmedi
            # Siparişi iptal edin
            PaymentService.paytr_logger.info(f"Order {merchant_oid} has been declined.")
            PaymentService.paytr_logger.info(f"Order {merchant_oid} has been canceled. Reason: {request.get('failed_reason_msg', 'Unknown reason')}")
            return False

    @staticmethod
    def success_payment(merchant_oid):
        provision = ProvisionService.get_provision_by_merchant_oid(merchant_oid)


        # Eğer provision bulunduysa, abonelik kaydı yap
        if provision:
            package = PackageService.get_package_by_id(provision.package_id)
            # Abonelik tarihlerini ayarla
            subscription_date = datetime.utcnow()

            if provision.is_annual:
                subscription_end_date = subscription_date + timedelta(days=365)  # 30 gün sonrasına bitiş tarihi ekleniyor
            else:
                subscription_end_date = subscription_date + timedelta(days=30)  # 30 gün sonrasına bitiş tarihi ekleniyor

            if provision.used_coupon:
                used_coupon = provision.used_coupon
                CouponService.use_coupon(used_coupon, provision.user_id)
            else:
                used_coupon = None

            # Yeni Subscription kaydı oluştur
            subscription = Subscription(
                subscription_date=subscription_date,
                subscription_end_date=subscription_end_date,
                credit_balance=package["credits"],  # Başlangıç için varsayılan kredi bakiyesi
                discord_id=None,
                discord_username=None,
                user_id=provision.user_id,
                username=provision.username,
                merchant_oid=merchant_oid,
                email=provision.email,
                max_credit_balance=int(package["credits"]),
                used_coupon=used_coupon,
                package=package["title"]
            )

            purchase = Purchase(
                username= provision.username,
                package= package["title"],
                amount= provision.amount
            )



            try:
                # Veritabanına kaydet
                subscription.save()
                purchase.save()

                provision.delete()

                PaymentService.paytr_logger.info(f"Subscription created for user {provision.username} with merchant_oid {merchant_oid}")
                return True
            except Exception as e:
                PaymentService.paytr_logger.info(f"Error saving subscription: {str(e)}")
                return False

        else:
            PaymentService.paytr_logger.error(f"Provision not found for merchant_oid: {merchant_oid}")
            return False

    # Metin dosyasını okuma fonksiyonu (static klasöründen)
    @staticmethod
    def read_contract_file(language):
        # Static klasöründeki dosya yolunu oluşturuyoruz
        file_path = os.path.join(current_app.static_folder, 'contracts', f'remote_sales_contract_{language}.txt')

        # Dosya mevcutsa okuma işlemi
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        else:
            return None
