from flask import Blueprint, request, jsonify

from app.auth import jwt_required
from app.services.support_service import log_support_request

support_bp = Blueprint('support_bp', __name__)

@support_bp.route('/create-support', methods=['POST'])
@jwt_required(pass_payload=True)
def support_request(payload):
    data = request.json

    # Gelen veriyi kontrol et
    name = data.get('name')
    message = data.get('message')

    if not name or not message:
        return jsonify({"error": "Name and message are required"}), 400

    # Servis ile log kaydı yap
    try:
        log_support_request(name, message, payload)
        return jsonify({"message": "Support request received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
