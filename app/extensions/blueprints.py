import os
from datetime import datetime, timedelta

from flask import send_from_directory, current_app, jsonify, request
import logging
import json

from app.auth import jwt_required, verify_jwt_token
from app.models.subscription_model import Subscription
from app.models.user_model import User
from app.routes.admin_routes import admin_routes_bp
from app.routes.announcement_rotes import announcement_bp
from app.routes.coupon_routes import coupon_bp
from app.routes.enterprise.enterprise_routes import enterprise_bp
from app.routes.gallery_routes import gallery_routes_bp
from app.routes.image_to_image_routes import image_to_image_bp
from app.routes.mail_routes import mail_bp
from app.routes.payment_routes import payment_bp
from app.routes.support_routes import support_bp
from app.routes.upscale_routes import upscale_bp
from app.routes.user_routes import user_bp
from app.routes.package_routes import package_bp
from app.routes.text_to_image_routes import text_to_image_bp
from app.routes.video_generation_routes import video_generation_bp
from app.services.enterprise.enterprise_service import EnterpriseService
from app.services.image_to_image_service import ImageToImageService
from app.services.text_to_image_service import TextToImageService
from app.services.upscale_service import UpscaleService
from app.services.video_generation_service import VideoGenerationService
from app.utils.notification import notify_user_via_websocket
from app.utils.queue_manager import redis_conn

from PyPDF2 import PdfReader


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
    app.register_blueprint(video_generation_bp, url_prefix='/video_generation')
    app.register_blueprint(support_bp, url_prefix='/support')
    app.register_blueprint(image_to_image_bp, url_prefix='/imagetoimage')
    app.register_blueprint(gallery_routes_bp, url_prefix='/gallery')
    app.register_blueprint(announcement_bp, url_prefix='/announcements')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/logo.png')
    def serve_logo():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'logo.png')

    @app.route('/banner.png')
    def serve_banner():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'banner.png')

    @app.route('/robots.txt')
    def robots_txt():
        return send_from_directory(app.static_folder, 'robots.txt')

    @app.route('/campaign/assign-credits', methods=['POST'])
    @jwt_required(pass_payload=False)
    def assign_credit():
        """
        Kullanıcıya kredi tanımlama işlemini gerçekleştirir.
        """
        try:
            # İstekten JSON verilerini al
            data = request.get_json()
            user_id = data.get('userId')
            credit = data.get('credit')

            # User ID ile veritabanından kullanıcıyı sorgula (örneğin User modelini kullanarak)
            # (Bu kısımda mevcut bir kullanıcıyı doğrulamak isteyebilirsiniz.)
            user = User.objects(id=user_id).first()
            if not user:
                return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404


            # Subscription nesnesini oluştur
            subscription = Subscription(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                subscription_date=datetime.utcnow(),
                subscription_end_date=datetime.utcnow() + timedelta(days=60),
                credit_balance=float(credit),
                merchant_oid="HORIAR-UNIVERSITE-KAMPANYASI",  # Manuel eklemelerde özel bir tanımlama
                used_coupon=None,  # İsteğe bağlı olarak kullanılabilir,
                max_credit_balance=int(credit)
            )

            # Yeni abonelik kaydını veritabanına kaydet
            subscription.save()

            return jsonify({"success": True, "message": "Kredi başarıyla tanımlandı!"}), 200

        except Exception as e:
            logging.error(f"Kredi tanımlama hatası: {str(e)}")
            return jsonify({"success": False, "message": "Kredi tanımlama sırasında bir hata oluştu"}), 500

    # Dosya uzantısı kontrolü
    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'pdf'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/upload-scenerio', methods=['POST'])
    def upload_scenerio():
        if 'file' not in request.files:
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        if file and allowed_file(file.filename):
            try:
                # PDF'i oku
                pdf_reader = PdfReader(file)
                text = ""

                # Her sayfayı oku
                for page in pdf_reader.pages:
                    text += page.extract_text()

                return jsonify({'success': True, 'text': text})

            except Exception as e:
                return jsonify({'error': f'PDF okuma hatası: {str(e)}'}), 500

        return jsonify({'error': 'İzin verilmeyen dosya türü'}), 400

    @app.route('/webhook', methods=['POST'])
    def runpod_webhook():
        """
        RunPod tamamlanan işler için webhook endpoint'i.
        """
        try:
            data = request.get_json()
            if data is None:
                # Eğer JSON değilse request.data kullanarak manuel olarak parse edelim
                raw_data = request.data

                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON from raw data: {e}")
                    return jsonify({"error": "Invalid JSON format"}), 400


            # İşi tamamlayan job_id ve output bilgilerini alıyoruz
            job_id = data.get("id")
            status = data.get("status")
            output = data.get("output")


            # Redis'ten ilgili job_id'yi alarak kaydı kontrol et
            request_key = f"runpod_request:{job_id}"
            stored_data = redis_conn.get(request_key)

            if redis_conn.exists(request_key):
                logging.info(f"Key {request_key} exists in Redis")
            else:
                logging.info(f"Key {request_key} does not exist in Redis")


            if not stored_data:
                logging.warning(f"No pending request found for job_id: {job_id}")
                return jsonify({"message": f"No pending request found for job_id: {job_id}"}), 404

            # Redis'te bulunan veriyi çözümle ve iş durumu "COMPLETED" mi diye kontrol et
            request_info = json.loads(stored_data)
            user_id = request_info.get("user_id")
            job_type = request_info.get("job_type")


            if not job_id or not status:
                notify_user_via_websocket(user_id, {"status": "failed", "message": "A server error occurred while processing your request"})
                return jsonify({"message": "Invalid data"}), 400


            # İşlem tamamlandıysa iş türüne göre veritabanına kayıt işlemi yapalım
            if status == "COMPLETED":

                image_url = output.get("message")


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
                    message = {"status": status, "message": image_url, "model_type": request_info.get("model_type"),
                               "resolution":request_info.get("resolution"), "prompt_fix": request_info.get("prompt_fix") }

                elif job_type == "upscale":
                    UpscaleService.save_request_to_db(
                        response=data,  # RunPod yanıtı
                        user_id=user_id,
                        username=request_info.get("username"),
                        low_res_image=request_info.get("low_res_image_url"),
                        app=current_app
                    )
                    message = {"status": status, "message": image_url, "ref_image_url": request_info.get("low_res_image_url")}

                elif job_type == "text_to_video_generation":
                    VideoGenerationService.save_text_to_video_to_db(
                        user_id=user_id,
                        username=request_info.get("username"),
                        response=data,
                        prompt=request_info.get("prompt"),
                        model=request_info.get("model")
                    )
                    message = {"status": status, "message": image_url}

                elif job_type == "image_to_video_generation":
                    VideoGenerationService.save_image_to_video_to_db(
                        user_id=user_id,
                        username=request_info.get("username"),
                        response=data,
                        prompt=request_info.get("prompt"),
                        image_url= request_info.get("image_url"),
                    )
                    message = {"status": status, "message": image_url, "ref_image_url": request_info.get("image_url")}

                elif job_type == "image_to_image_generation":
                    ImageToImageService.save_request_to_db(
                        response=data,
                        user_id=user_id,
                        username=request_info.get("username"),
                        ref_image=request_info.get("ref_image"),
                        prompt=request_info.get("prompt"),
                        app=current_app
                    )
                    message = {"status": status, "message": image_url, "ref_image_url": request_info.get("ref_image"),
                               "prompt": request_info.get("prompt") }

                elif job_type == "customer_image_generation":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="text-to-image",
                        model_type=request_info.get("model_type"),
                        prompt=request_info.get("prompt"),
                        seed=str(request_info.get("seed")),
                        resolution=request_info.get("resolution"),
                        response=data,
                        low_res_url=None,
                        ref_image=None,
                        request_id=request_info.get("request_id"),
                        consistent=None
                    )
                    redis_conn.unlink(request_key)
                    return "customer_image_generation", 200

                elif job_type == "customer_upscale":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="upscale",
                        model_type=None,
                        prompt=None,
                        seed=None,
                        resolution=None,
                        response=data,
                        ref_image=None,
                        low_res_url=request_info.get("low_res_image_url"),
                        request_id=request_info.get("request_id"),
                        consistent=None
                    )
                    redis_conn.unlink(request_key)
                    return "customer_upscale", 200

                elif job_type == "customer_text_to_video":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="text-to-video",
                        model_type=None,
                        prompt=request_info.get("prompt"),
                        seed=None,
                        resolution=None,
                        response=data,
                        low_res_url=None,
                        ref_image=None,
                        request_id=request_info.get("request_id"),
                        consistent=None
                    )
                    redis_conn.unlink(request_key)
                    return "customer_text_to_video", 200

                elif job_type == "customer_image_to_video":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="image-to-video",
                        model_type=None,
                        prompt=request_info.get("prompt"),
                        seed=None,
                        resolution=None,
                        response=data,
                        ref_image=request_info.get("ref_image"),
                        low_res_url=request_info.get("low_res_image_url"),
                        request_id=request_info.get("request_id"),
                        consistent=None
                    )
                    redis_conn.unlink(request_key)
                    return "customer_image_to_video", 200

                else:
                    message = {"status": "failed", "message": "İstek sırasında bir hata ile karşılaşıldı.", "ref_image_url": None}

                # Kullanıcıya bildirim gönder (frontend'e WebSocket ile veya diğer yöntemlerle)
                notify_user_via_websocket(user_id, message)
                logging.info(f"Job {job_id} completed with image URL: {image_url}")

                # Redis'ten veriyi sil
                redis_conn.unlink(request_key)
                if redis_conn.exists(request_key):
                    logging.info(f"Key {request_key} exists in Redis")
                else:
                    logging.info(f"Key {request_key} does not exist in Redis")

                return jsonify(message), 200

            else:

                logging.info("not completed")

                if job_type == "customer_image_generation":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db_error(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="text-to-image",
                        request_id=request_info.get("request_id"),
                        error_message= "A server error occurred while processing your request"

                    )
                    return "customer_image_generation with error", 200

                elif job_type == "customer_upscale":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db_error(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="upscale",
                        request_id=request_info.get("request_id"),
                        error_message= "A server error occurred while processing your request"
                    )
                    return "customer_upscale with error", 200

                elif job_type == "customer_text_to_video":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db_error(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="text-to-video",
                        request_id=request_info.get("request_id"),
                        error_message= "A server error occurred while processing your request"
                    )
                    return "customer_text_to_video with error", 200

                elif job_type == "customer_image_to_video":
                    enterpriseService = EnterpriseService()
                    enterpriseService.save_request_to_db_error(
                        customer_id=request_info.get("customer_id"),
                        company_name=request_info.get("company_name"),
                        request_type="image-to-video",
                        request_id=request_info.get("request_id"),
                        error_message= "A server error occurred while processing your request"
                    )
                    return "customer_image_to_video with error", 200

                else:
                    # Başarısız durum güncellemesi ve bildirim gönderme
                    request_info['status'] = status
                    redis_conn.set(request_key, json.dumps(request_info), ex=3600)
                    notify_user_via_websocket(user_id, {"status": "failed", "message": "A server error occurred while processing your request"})
                    logging.warning(f"Job {job_id} failed with status: {status}")
                    return jsonify({"message": f"Job {job_id} failed with status {status}"}), 200

        except Exception as e:
            raw_request_data = request.get_data(as_text=True)  # Gelen veriyi string formatında al
            logging.error(f"Error processing webhook: {str(e)}")
            logging.error(f"Request body at error: {raw_request_data}")  # Hatalı gelen veriyi log'la
            logging.info(f"-------------------------------------------------------------------------------------")
            return jsonify({"message": f"Error processing webhook: {str(e)}"}), 500

    @app.route('/verify-token', methods=['GET'])
    @jwt_required(pass_payload=True)
    def verify_token(payload):
        """
        Bearer token'ın geçerli olup olmadığını kontrol eden endpoint.
        """
        if payload:
            return jsonify({"success": True, "message": "Token is valid"}), 200
        else:
            return jsonify({"success": False, "message": "Token is invalid"}), 401


