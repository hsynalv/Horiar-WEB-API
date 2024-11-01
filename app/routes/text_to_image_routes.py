from flask import Blueprint, request, jsonify, current_app
from app.services.text_to_image_service import TextToImageService
from app.middlewares import daily_request_limit, ban_check, check_credits, jwt_or_ip_required

from ..auth import jwt_required
import logging

text_to_image_bp = Blueprint('text_to_image_bp', __name__)

@text_to_image_bp.route('/generate-image-direct', methods=['POST'])
@jwt_required(pass_payload=True)
@ban_check
@check_credits(1)
def generate_image_direct(payload):
    data = request.json

    # Kullanıcıya özel oda adı olarak user_id kullanılıyor
    room = payload.get("sub")  # JWT payload'dan kullanıcı ID'sini alıyoruz

    prompt = data.get('prompt')
    model_type = data.get('model_type', None)
    resolution = data.get('resolution', None)
    prompt_fix = data.get('prompt_fix', True)

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    # Kuyruğa göre image generation işlemini başlatma
    job = TextToImageService.generate_image_with_queue(prompt, model_type, resolution, payload,
                                    prompt_fix, False, room)

    return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

@text_to_image_bp.route('/generate-image-direct-consistent', methods=['POST'])
@jwt_required(pass_payload=True)
@ban_check
@check_credits(1)
def generate_image_direct_consistent(payload):
    data = request.json

    # Kullanıcıya özel oda adı olarak user_id kullanılıyor
    room = payload.get("sub")  # JWT payload'dan kullanıcı ID'sini alıyoruz

    prompt = data.get('prompt')
    model_type = data.get('model_type', None)
    resolution = data.get('resolution', None)
    prompt_fix = data.get('prompt_fix', True)

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    # Kuyruğa göre image generation işlemini başlatma
    job = TextToImageService.generate_image_with_queue(prompt, model_type, resolution, payload,
                                                       prompt_fix, True, room)

    return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

@text_to_image_bp.route('/requests/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_requests_by_user(user_id):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa

    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = TextToImageService.get_requests_by_user_id(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500

@text_to_image_bp.route('/requests/consistent/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_requests_by_user_consistent(user_id):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa

    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = TextToImageService.get_requests_by_user_id_consistent(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500



