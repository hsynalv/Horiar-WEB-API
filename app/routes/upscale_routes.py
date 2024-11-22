# upscale_routes.py
import logging

from flask import Blueprint, jsonify, request, current_app

from app.auth import jwt_required
from app.middlewares import check_credits
from app.models.text_to_image_model import TextToImage
from app.services.upscale_service import UpscaleService
from app.utils.convert_to_webp import process_and_save_image, download_image

# Blueprint oluşturuluyor
upscale_bp = Blueprint('upscale_bp', __name__)


@upscale_bp.route('/enhance', methods=['POST'])
@jwt_required(pass_payload=True)
@check_credits(5)
def create_upscale(payload):
    """
    Yeni bir upscale talebi oluşturur.
    """
    logging.info("upscale route girildi")

    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file part"}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if image_file:
            image_bytes = image_file.read()

            # Kullanıcıya özel oda adı olarak user_id'yi kullanıyoruz
            room = payload.get("sub")  # JWT payload'dan kullanıcı ID'sini alıyoruz

            # Kuyruğa ekleme
            job = UpscaleService.add_to_upscale_queue(
                image_bytes=image_bytes, payload=payload, room=room
            )

            return jsonify({"message": "Upscale request has been queued", "job_id": job.id, "room": room}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@upscale_bp.route('/enhance-link', methods=['POST'])
@jwt_required(pass_payload=True)
@check_credits(5)
def create_upscale_from_link(payload):
    """
    Yeni bir upscale talebi oluşturur.
    """
    data = request.json
    image_link = data.get("image-link")

    if not image_link:
        return jsonify({"error": "Image Link is required"}), 400

    try:
        bytes_IO = download_image(image_link)
        image_bytes = bytes_IO.getvalue()

        # Kullanıcıya özel oda adı olarak user_id'yi kullanıyoruz
        room = payload.get("sub")  # JWT payload'dan kullanıcı ID'sini alıyoruz
        # Kuyruğa ekleme
        job = UpscaleService.add_to_upscale_queue(
            image_bytes=image_bytes, payload=payload, room=room
        )

        return jsonify({"message": "Upscale request has been queued", "job_id": job.id, "room": room}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@upscale_bp.route('/enhance/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_upscale_by_user(user_id):
    """
    Belirtilen ID'ye göre bir upscale talebini getirir.
    """
    page = int(request.args.get('page', 1))  # Varsayılan olarak 1. sayfa


    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = UpscaleService.get_upscale_request_by_userid(user_id, page)

        # Sonuçları JSON formatında döndür
        return jsonify(requests), 200

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500

@upscale_bp.route('/enhance/request/<upscale_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_upscale_by_id(upscale_id):
    """
    Belirtilen ID'ye göre tek bir upscale talebini getirir.
    """
    try:
        # ID'ye göre tek bir upscale talebini al
        request = UpscaleService.get_by_id(upscale_id)

        custom_request = {
            "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
            "low_res_image_url": request.low_res_image_url,
            "high_res_image_url": request.image_url_webp,
            "high_image_png": request.high_res_image_url,
        }

        if request:
            return jsonify(custom_request), 200
        else:
            return jsonify({"error": "Upscale request not found"}), 404

    except Exception as e:
        # Hata durumunda hata mesajı döndür
        return jsonify({"error": str(e)}), 500

@upscale_bp.route('/upscales', methods=['GET'])
def get_all_upscales():
    """
    Tüm upscale taleplerini getirir.
    """
    try:
        upscale_requests = UpscaleService.get_all_upscale_requests()
        return jsonify([upscale.to_dict() for upscale in upscale_requests]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

