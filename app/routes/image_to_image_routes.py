import logging

from flask import Blueprint, request, jsonify

from app.auth import jwt_required
from app.middlewares import check_credits
from app.services.image_to_image_service import ImageToImageService

image_to_image_bp = Blueprint("image_to_image_bp", __name__)

@image_to_image_bp.route('/create', methods=['POST'])
@jwt_required(pass_payload=True)
@check_credits(5)
def create(payload):
    """
    Yeni bir upscale talebi oluşturur.
    """
    logging.info("upscale route girildi")

    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file part"}), 400

        prompt = request.form.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if image_file:
            image_bytes = image_file.read()

            # Kullanıcıya özel oda adı olarak user_id'yi kullanıyoruz
            room = payload.get("sub")  # JWT payload'dan kullanıcı ID'sini alıyoruz

            # Kuyruğa ekleme
            job = ImageToImageService.add_to_image_to_image_queue(
                image_bytes=image_bytes, prompt=prompt,payload=payload, room=room
            )

            return jsonify({"message": "Upscale request has been queued", "job_id": job.id, "room": room}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@image_to_image_bp.route('/getbyuser/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_request_by_user(user_id):
    """
    Belirtilen ID'ye göre bir upscale talebini getirir.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa


    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = ImageToImageService.get_request_by_userid(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500

@image_to_image_bp.route('/getbyid/<upscale_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_upscale_by_id(upscale_id):
        """
        Belirtilen ID'ye göre tek bir upscale talebini getirir.
        """
        try:
            # ID'ye göre tek bir upscale talebini al
            request = ImageToImageService.get_by_id(upscale_id)

            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "ref_image": request.ref_image,
                "image_url_webp": request.image_url_webp,
                "image": request.image,
                "prompt": request.prompt
            }

            if request:
                return jsonify(custom_request), 200
            else:
                return jsonify({"error": "Upscale request not found"}), 404

        except Exception as e:
            # Hata durumunda hata mesajı döndür
            return jsonify({"error": str(e)}), 500