from flask import Blueprint, request, jsonify, current_app
from app.services.text_to_image import TextToImageService

from ..auth import jwt_required

text_to_image_bp = Blueprint('text_to_image', __name__)

@text_to_image_bp.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Text to image kuyruğuna ekle ve sonucu bekle
        result = TextToImageService.add_to_queue(current_app._get_current_object(), prompt)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_to_image_bp.route('/generate-image-direct', methods=['POST'])
@jwt_required(pass_payload=True)
def generate_image_direct(payload):
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


@text_to_image_bp.route('/requests', methods=['GET'])
@jwt_required(pass_payload=True)
def get_requests_by_user(payload):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = TextToImageService.get_requests_by_user_id(current_app, payload)

        # Sonuçları JSON formatında döndür
        return jsonify([request.to_dict() for request in requests]), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500
