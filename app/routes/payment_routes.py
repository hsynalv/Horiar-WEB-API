from flask import Blueprint, current_app, request

from app.auth import jwt_required
from app.services.package_service import PackageService
from app.services.payment_service import PaymentService
from app.services.user_service import UserService

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/get-token', methods=['POST'])
@jwt_required(pass_payload=True)
def get_token(payload):
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data = request.json
    package_id = data.get('package_id')
    user_address = data.get('user_address')
    user_phone = data.get('user_phone')
    print(user_ip)
    result = PaymentService.get_token(current_app._get_current_object(), payload, package_id, user_address, user_phone, user_ip)
    return result