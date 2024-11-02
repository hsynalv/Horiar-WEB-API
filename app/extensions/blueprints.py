import logging
import os

from flask import send_from_directory, current_app

from app.extensions.socketio import notify_user_via_websocket
from app.routes.admin_routes import admin_routes_bp
from app.routes.coupon_routes import coupon_bp
from app.routes.enterprise.enterprise_routes import enterprise_bp
from app.routes.mail_routes import mail_bp
from app.routes.payment_routes import payment_bp
from app.routes.upscale_routes import upscale_bp
from app.routes.user_routes import user_bp
from app.routes.package_routes import package_bp
from app.routes.text_to_image_routes import text_to_image_bp
from app.services.text_to_image_service import TextToImageService
from app.services.upscale_service import UpscaleService
from app.utils.queue_manager import redis_conn


def register_blueprints(app):
    # Parent Blueprint tanımlaması

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(package_bp, url_prefix='/package')
    app.register_blueprint(text_to_image_bp, url_prefix='/v1/create')
    app.register_blueprint(upscale_bp, url_prefix='/v1/upscale')
    app.register_blueprint(coupon_bp, url_prefix='/coupon')
    app.register_blueprint(mail_bp)
    app.register_blueprint(admin_routes_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(enterprise_bp, url_prefix='/enterprise')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/robots.txt')
    def robots_txt():
        return send_from_directory(app.static_folder, 'robots.txt')

    from flask import jsonify, request
    import logging
    import json

    @app.route('/webhook', methods=['POST'])
    def runpod_webhook():
        """
        RunPod tamamlanan işler için webhook endpoint'i.
        """
        try:
            data = request.json  # Gelen JSON veriyi alıyoruz
            logging.info(f"Webhook received data: {data}")

            # İşi tamamlayan job_id ve output bilgilerini alıyoruz
            job_id = data.get("id")
            status = data.get("status")
            output = data.get("output")

            # Redis'ten ilgili job_id'yi alarak kaydı kontrol et
            request_key = f"runpod_request:{job_id}"
            stored_data = redis_conn.get(request_key)

            # Redis'te bulunan veriyi çözümle ve iş durumu "COMPLETED" mi diye kontrol et
            request_info = json.loads(stored_data)
            user_id = request_info.get("user_id")
            job_type = request_info.get("job_type")
            image_url = output.get("message")

            if not job_id or not status or not output:
                notify_user_via_websocket(user_id, {"status": "failed", "message": "A server error occurred while processing your request"})
                return jsonify({"message": "Invalid data"}), 400


            if not stored_data:
                logging.warning(f"No pending request found for job_id: {job_id}")
                return jsonify({"message": f"No pending request found for job_id: {job_id}"}), 404



            # İşlem tamamlandıysa iş türüne göre veritabanına kayıt işlemi yapalım
            if status == "COMPLETED":
                # İş türüne göre ilgili kayıt fonksiyonunu çağır
                if job_type == "image_generation":
                    TextToImageService.save_request_to_db(
                        user_id=user_id,
                        username=request_info.get("username"),
                        prompt=request_info.get("prompt"),
                        response=data,  # RunPod yanıtı
                        seed=request_info.get("seed"),
                        model_type=request_info.get("model_type"),
                        resolution=request_info.get("resolution"),
                        randomSeed=request_info.get("consistent"),
                        app=current_app,
                        prompt_fix=request_info.get("prompt_fix")
                    )


                elif job_type == "upscale":
                    UpscaleService.save_request_to_db(
                        response=data,  # RunPod yanıtı
                        user_id=user_id,
                        username=request_info.get("username"),
                        low_res_image=request_info.get("low_res_image_url"),
                        app=current_app
                    )
                """
                elif job_type == "video_generation":
                    VideoService.save_request_to_db(
                        user_id=user_id,
                        video_url=image_url,
                        # Gerekli diğer alanları ekle
                    )
                """

                # Kullanıcıya bildirim gönder (frontend'e WebSocket ile veya diğer yöntemlerle)
                notify_user_via_websocket(user_id, {"status": status, "message": image_url})
                logging.info(f"Job {job_id} completed with image URL: {image_url}")
                return jsonify({"message": "Webhook received successfully"}), 200

            else:
                # Başarısız durum güncellemesi ve bildirim gönderme
                request_info['status'] = status
                redis_conn.set(request_key, json.dumps(request_info), ex=3600)
                notify_user_via_websocket(user_id, {"status": "failed", "message": "A server error occurred while processing your request"})
                logging.warning(f"Job {job_id} failed with status: {status}")
                return jsonify({"message": f"Job {job_id} failed with status {status}"}), 200

        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}")
            return jsonify({"message": f"Error processing webhook: {str(e)}"}), 500



