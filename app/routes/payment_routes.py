import logging

from flask import Blueprint, current_app, request, jsonify
from flask_wtf import CSRFProtect
from app.auth import jwt_required
from app.services.package_service import PackageService
from app.services.payment_service import PaymentService
from app.services.user_service import UserService
import base64
import hashlib
import hmac

payment_bp = Blueprint('payment_bp', __name__)

csrf = CSRFProtect()

@payment_bp.route('/get-token', methods=['POST'])
@jwt_required(pass_payload=True)
def get_token(payload):
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data = request.json
    package_id = data.get('package_id')
    user_address = data.get('user_address')
    user_phone = data.get('user_phone')
    is_annual = data.get('is_annual')
    name_surname = data.get('name_surname')
    coupon_name = data.get('coupon_name')
    result = PaymentService.get_token(current_app._get_current_object(), payload, package_id, user_address, user_phone, user_ip, is_annual, name_surname, coupon_name)
    return result


@payment_bp.route('/callback-ok', methods=['POST'])
@csrf.exempt  # CSRF korumasını devre dışı bırak
def callback_ok():
    print("callback ok girildi")
    # Sadece POST isteklerini kabul et
    if request.method != 'POST':
        return '', 400  # Bad Request

    print("method post methodu")

    post = request.form
    # API Entegrasyon Bilgileri
    merchant_key = b'tPXEJcsryeF34ER5'
    merchant_salt = 'bS8chedC5bDcLC7s'
    # POST değerleri ile hash oluştur.
    hash_str = post['merchant_oid'] + merchant_salt + post['status'] + post['total_amount']
    hash = base64.b64encode(hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()).decode()

    print("hash çıkartıldı")

    # Oluşturulan hash'i, paytr'dan gelen post içindeki hash ile karşılaştır
    if hash != post['hash']:
        return 'PAYTR notification failed: bad hash', 400  # Bad Request
    # Siparişin durumunu kontrol et
    merchant_oid = post['merchant_oid']
    status = post['status']
    # Burada siparişi veritabanından sorgulayıp onaylayabilir veya iptal edebilirsiniz.
    if status == 'success':  # Ödeme Onaylandı
        # Siparişi onaylayın
        print(f"Order {merchant_oid} has been approved.")
        # Müşteriye bildirim yapabilirsiniz (SMS, e-posta vb.)
        # Güncel tutarı post['total_amount'] değerinden alın.
    else:  # Ödemeye Onay Verilmedi
        # Siparişi iptal edin
        print(f"Order {merchant_oid} has been canceled. Reason: {post.get('failed_reason_msg', 'Unknown reason')}")
    # Bildirimin alındığını PayTR sistemine bildir.
    return 'OK', 200  # OK


"""
@payment_bp.route('/callback-ok', methods=['POST'])
@csrf.exempt  # CSRF korumasını devre dışı bırak
def callback_ok():
    logging.info("callback fonksiyonuna girildi")
    post = request.form

    result = PaymentService.callback_ok_funciton(current_app._get_current_object(), post)

    if result:  # Ödeme Onaylandı
        return 'OK', 200  # OK
    else:  # Ödemeye Onay Verilmedi
        return '', 404
"""