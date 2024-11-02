from flask import Blueprint, request, jsonify

from app.auth import jwt_required
from app.middlewares import ban_check, check_credits
from app.services.video_generation_service import VideoGenerationService

video_generation_bp = Blueprint('video_generation_bp', __name__)

@video_generation_bp.route('/text-to-video', methods=['POST'])
@jwt_required(pass_payload=True)
@ban_check
@check_credits(15)
def generate_text_to_video(payload):
    data = request.json

    room = payload.get("sub")
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    # Kuyruğa göre video generation işlemini başlatma
    job = VideoGenerationService.generate_video_with_queue(prompt, payload, room)

    return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

@video_generation_bp.route('/text-to-video/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_requests_by_user(user_id):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa

    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = VideoGenerationService.get_text_to_video_by_user_id(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500