from flask import Blueprint, request, jsonify, current_app
from app.services.text_to_image_service import TextToImageService
from app.middlewares import daily_request_limit, ban_check

from ..auth import jwt_required

text_to_image_bp = Blueprint('text_to_image_bp', __name__)

@text_to_image_bp.route('/generate-image-direct', methods=['POST', 'OPTIONS'])
@jwt_required(pass_payload=True)
@daily_request_limit
@ban_check
def generate_image_direct(payload):
    if request.method == 'OPTIONS':
        # Preflight OPTIONS isteğine 200 OK ile yanıt dönüyoruz
        response = current_app.response_class(
            status=200,
            headers={
                'Access-Control-Allow-Origin': 'https://www.horiar.com',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        return response
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Text to image işlemini kuyruk kullanmadan doğrudan yap
        result = TextToImageService.generate_image_directly(current_app._get_current_object(), prompt, payload)

        # Eğer result JSON değilse, burada hata olabilir
        return jsonify(result), 200
    except Exception as e:
        print(f"Error: {e}")  # Hata mesajı
        return jsonify({"message": str(e)}), 500


@text_to_image_bp.route('/requests/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_requests_by_user(user_id):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = TextToImageService.get_requests_by_user_id(user_id)

        # Sonuçları JSON formatında döndür
        return jsonify([request.to_dict() for request in requests]), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500
