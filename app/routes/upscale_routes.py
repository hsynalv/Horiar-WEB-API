# upscale_routes.py
import logging

from flask import Blueprint, jsonify, request, current_app

from app.auth import jwt_required
from app.middlewares import check_credits
from app.models.text_to_image_model import TextToImage
from app.services.upscale_service import UpscaleService
from app.utils.convert_to_webp import process_and_save_image

# Blueprint oluşturuluyor
upscale_bp = Blueprint('upscale_bp', __name__)


@upscale_bp.route('/enhance', methods=['POST'])
@jwt_required(pass_payload=True)
@check_credits(5)
def create_upscale(payload):
    """
    Yeni bir upscale talebi oluşturur.
    Bu rota, front-end'den gelen düşük çözünürlüklü bir resmi alır ve upscale işlemini başlatır.
    """
    logging.info("upscale route girildi")

    try:
        # İmajı request'ten almak
        if 'image' not in request.files:
            return jsonify({"error": "No image file part"}), 400

        image_file = request.files['image']
        # Eğer dosya ismi boş ise, kullanıcı dosya seçmemiş demektir
        if image_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if image_file:
            # Resim dosyasını istediğiniz işlemleri yapmak üzere okuyabilirsiniz
            image_bytes = image_file.read()  # Bu binary veriyi işlemek için kullanabilirsiniz

            # Yeni upscale isteği oluşturuluyor
            upscale_request = UpscaleService.create_upscale_request(app = current_app._get_current_object(),low_res_image=image_bytes, payload=payload)

            return upscale_request, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@upscale_bp.route('/enhance/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_upscale_by_user(user_id):
    """
    Belirtilen ID'ye göre bir upscale talebini getirir.
    """
    try:
        # Kullanıcı ID'sine göre istekleri al
        requests = UpscaleService.get_upscale_request_by_userid(user_id)

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

