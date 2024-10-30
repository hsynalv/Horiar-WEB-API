import logging
import os

from flask import send_from_directory, request, jsonify, Blueprint

from app.routes.admin_routes import admin_routes_bp
from app.routes.coupon_routes import coupon_bp
from app.routes.enterprise.enterprise_routes import enterprise_bp
from app.routes.mail_routes import mail_bp
from app.routes.payment_routes import payment_bp
from app.routes.upscale_routes import upscale_bp
from app.routes.user_routes import user_bp
from app.routes.package_routes import package_bp
from app.routes.text_to_image_routes import text_to_image_bp

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


    @app.route('/webhook', methods=['POST'])
    def runpod_webhook():
        """
        RunPod tamamlanan işler için webhook endpoint'i.
        """
        try:
            data = request.json  # Gelen JSON veriyi alıyoruz
            logging.info(data)

            # İşi tamamlayan job_id ve output bilgilerini alıyoruz
            job_id = data.get("id")
            status = data.get("status")
            output = data.get("output")

            if not job_id or not status or not output:
                return jsonify({"message": "Invalid data"}), 400

            # İş durumu "COMPLETED" mi diye kontrol edelim
            if status == "COMPLETED":
                # Output'tan gerekli bilgileri al
                image_url = output.get("message")

                # Eğer iş başarılı bir şekilde tamamlandıysa, burada işleme devam edebiliriz
                # Örneğin, bu URL'yi veritabanına kaydedebiliriz veya kullanıcılara bildirim gönderebiliriz.
                logging.info(f"Job {job_id} completed with image URL: {image_url}")

                # Burada veritabanına kaydetme işlemi yapabiliriz.
                # TextToImageService.save_request_to_db(user_id, ...)

                return jsonify({"message": "Webhook received successfully"}), 200
            else:
                logging.warning(f"Job {job_id} failed with status: {status}")
                return jsonify({"message": f"Job {job_id} failed with status {status}"}), 200

        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}")
            return jsonify({"message": f"Error processing webhook: {str(e)}"}), 500


