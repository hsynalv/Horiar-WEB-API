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
    job = VideoGenerationService.generate_text_to_video_with_queue(prompt, payload, room)

    return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

@video_generation_bp.route('/image-to-video', methods=['POST'])
@jwt_required(pass_payload=True)
@ban_check
@check_credits(15)
def generate_image_to_video(payload):
    room = payload.get("sub")
    prompt = request.form.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    if 'image' not in request.files:
        return jsonify({"error": "No image file part"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if image_file:
        image_bytes = image_file.read()

        # Kuyruğa göre video generation işlemini başlatma
        job = VideoGenerationService.generate_image_to_video_with_queue(prompt, payload, image_bytes, room)

        return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

    return 400

@video_generation_bp.route('/image-to-video/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_image_to_video_requests_by_user(user_id):
    """
    JWT'den alınan kullanıcı ID'sine göre tüm istekleri döndürür.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa

    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = VideoGenerationService.get_image_to_video_by_user_id(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500

@video_generation_bp.route('/text-to-video/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_text_to_video_requests_by_user(user_id):
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