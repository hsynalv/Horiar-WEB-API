# upscale_routes.py

from flask import Blueprint, jsonify, request, current_app

from app.auth import jwt_required
from app.services.upscale_service import UpscaleService

# Blueprint oluşturuluyor
upscale_bp = Blueprint('upscale_bp', __name__)


@upscale_bp.route('/enhance', methods=['POST'])
@jwt_required(pass_payload=True)
def create_upscale(payload):
    """
    Yeni bir upscale talebi oluşturur.
    Bu rota, front-end'den gelen düşük çözünürlüklü bir resmi alır ve upscale işlemini başlatır.
    """
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
        return jsonify([request.to_dict() for request in requests]), 200

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


@upscale_bp.route('/upscale/<upscale_id>', methods=['DELETE'])
def delete_upscale(upscale_id):
    """
    Belirtilen ID'ye göre bir upscale talebini siler.
    """
    try:
        result = UpscaleService.delete_upscale_request(upscale_id)
        if result:
            return jsonify({"message": "Upscale request deleted successfully"}), 200
        else:
            return jsonify({"error": "Upscale request not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
