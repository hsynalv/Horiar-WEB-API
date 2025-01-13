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
    try:
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        data = request.json
        package_id = data.get('package_id')
        user_address = data.get('user_address')
        user_phone = data.get('user_phone')
        is_annual = data.get('is_annual')
        name_surname = data.get('name_surname')
        coupon_name = data.get('coupon_name')

        logging.info("payment route girildi")
        logging.info(f"package_id: {package_id}")
        logging.info(f"user_address: {user_address}")
        logging.info(f"user_phone: {user_phone}")
        logging.info(f"is_annual: {is_annual}")
        logging.info(f"name_surname: {name_surname}")
        logging.info(f"coupon_name: {coupon_name}")
        logging.info(f"route bilgileri --------------------------")

        result = PaymentService.get_token(
            current_app._get_current_object(),
            payload,
            package_id,
            user_address,
            user_phone,
            user_ip,
            is_annual,
            name_surname,
            coupon_name
        )
        return result

    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError: {e}")
        return jsonify({"message": str(e)}), 404

    except ValueError as e:
        logging.error(f"ValueError: {e}")
        return jsonify({"message": str(e)}), 400

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"message": str(e)}), 500

@payment_bp.route('/callback-ok', methods=['POST'])
@csrf.exempt  # CSRF korumasını devre dışı bırak
def callback_ok():
    post = request.form

    result = PaymentService.callback_ok_funciton(current_app._get_current_object(), post)

    if result:  # Ödeme Onaylandı
        return 'OK', 200  # OK
    else:  # Ödemeye Onay Verilmedi
        return 'OK', 200


@payment_bp.route('/contract/', methods=['GET'])
def get_contract():

    # Kullanıcının Accept-Language başlığından dil tercihini alıyoruz
    accept_language = request.headers.get('Accept-Language', '')

    # Varsayılan dil İngilizce ('en')
    language = 'en'

    # Accept-Language'de Türkçe var mı diye kontrol ediyoruz
    if 'tr' in accept_language.lower():
        language = 'tr'

    # Dosyadan metni oku
    contract_text = PaymentService.read_contract_file(language)

    if contract_text:
        return jsonify({"contract": contract_text}), 200
    else:
        return jsonify({"error": "Language not supported or file not found"}), 400

