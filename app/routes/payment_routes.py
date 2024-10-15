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
    logging.info("callback fonksiyonuna girildi")
    post = request.form

    result = PaymentService.callback_ok_funciton(current_app._get_current_object(), post)

    if result:  # Ödeme Onaylandı
        return 'OK', 200  # OK
    else:  # Ödemeye Onay Verilmedi
        return '', 404
