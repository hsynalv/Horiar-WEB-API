import json
import logging
import os
import datetime
import uuid

from flask import jsonify
from rq.job import parse_job_id

from app.models.enterprise.enterprise_customer_model import EnterpriseCustomer
from app.models.enterprise.enterprise_request_model import EnterpriseRequest
from app.services.base_service import BaseService
import secrets

from app.services.text_to_image_service import TextToImageService
from app.services.upscale_service import UpscaleService
from app.services.video_generation_service import VideoGenerationService
from app.utils.notification import notify_status_update
from app.utils.queue_manager import add_to_image_queue, redis_conn, add_to_upscale_queue, add_to_video_queue
from app.utils.runpod_requets import send_runpod_request
from app.utils.convert_to_webp import upload_image_to_s3, process_and_save_image


class EnterpriseService(BaseService):
    model = EnterpriseCustomer

    def create_customer(self, customer_data):
        # Müşteri verilerini oluşturuyoruz
        new_customer = self.model(
            company_name=customer_data['company_name'],
            contact_email=customer_data['contact_email']
        )
        new_customer.save()  # Veritabanına kaydet

        response_data = new_customer.to_dict()
        return response_data

    def generate_api_key(self, length=32):
        """
        Güvenli bir şekilde API anahtarı üretir.
        """
        return secrets.token_urlsafe(length)[:length]

    def create_token(self, customer_id):
        # Müşteri bilgilerini al
        customer = self.model.objects(id=customer_id).first()
        if not customer:
            raise ValueError("Customer not found")

        # Yeni API anahtarını oluştur
        api_key = self.generate_api_key()

        # Müşterinin api_key alanını güncelle
        customer.api_key = api_key
        customer.save()

        return api_key

    def validate_api_key(self, api_key):
        """
        API anahtarını doğrular ve ilgili müşteriyi döndürür.
        """
        customer = self.model.objects(api_key=api_key).first()
        return customer

    # Text To Image

    def text_to_image(self, prompt, model_type, resolution, customer, prompt_fix, consistent, room):
        """Kuyruğa göre image generation işlemini başlatır."""
        guid = str(uuid.uuid4())
        logging.info(f"deneme guid i {guid}")
        logging.info(f"guid tipi {type(guid)}" )
        job = add_to_image_queue(
            EnterpriseService.run_image_generation,
            prompt=prompt, model_type=model_type, resolution=resolution, customer=customer, consistent=consistent,
            request_id=guid, prompt_fix=prompt_fix, room=room  # room parametresi yalnızca **kwargs olarak geçiliyor
        )
        return jsonify({"job_id": guid, "message": "Your request has been queued." })

    @staticmethod
    def run_image_generation(prompt, model_type, resolution, customer, prompt_fix, consistent, request_id, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_promptfix.json')

            # workflow.json dosyasını güncelle
            updated_workflow = TextToImageService.update_workflow_with_prompt(
                path=workflow_path, prompt=prompt, model_type=model_type,
                resolution=resolution, randomSeed=not consistent, prompt_fix=prompt_fix
            )
            seed = updated_workflow["input"]["workflow"]["112"]["inputs"]["noise_seed"]


            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=str(customer.id), username=customer.company_name,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_URL",
                timeout=360
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "prompt": prompt,
                    "seed": seed,
                    "model_type": model_type,
                    "resolution": resolution,
                    "room": str(customer.id),
                    "status": "IN_PROGRESS",
                    "prompt_fix": prompt_fix,
                    "consistent": consistent,
                    "job_type": "customer_image_generation",
                    "customer_id": str(customer.id),
                    "company_name": customer.company_name,
                    "request_id": request_id
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your image generation request could not be processed.')
                logging.error(f"(Enterprise)Image generation request for user {str(customer.id)} failed with status: {result.get('status')}")
                return {"message": "Image generation request failed. Please try again later."}, 500

        return result


    # Upscale Enhance

    @staticmethod
    def upscale(image_bytes, customer, room):
        """Kuyruğa göre upscale işlemini başlatır."""
        guid = str(uuid.uuid4())
        job = add_to_upscale_queue(
            EnterpriseService.run_upscale,
            image_bytes=image_bytes, customer=customer, room=room, request_id=guid
        )
        notify_status_update(room, 'processing', 'Your upscale request is being processed.')
        return jsonify({"job_id": guid, "message": "Your request has been queued." })

    @staticmethod
    def run_upscale(image_bytes, customer, request_id, room = None):
        """Upscale işlemini çalıştırır ve Redis'te takip eder."""
        from app import create_app
        app = create_app()

        with app.app_context():
            customer_id = str(customer.id)
            company_name = str(customer.company_name)

            workflow_path = os.path.join(os.getcwd(), 'app/workflows/upscale_workflow.json')
            updated_workflow = UpscaleService.update_workflow(workflow_path, image_bytes)
            low_res_image_url = upload_image_to_s3(
                app=app, image_bytes=image_bytes, userid=customer_id, s3_folder_name="S3_FOLDER_UPSCALE_IMAGE",
                file_extension="png"
            )

            result, status_code = send_runpod_request(
                app=app, user_id=customer_id, username=company_name, data=json.dumps(updated_workflow),
                runpod_url="RUNPOD_UPSCALE_URL", timeout=600
            )

            # RunPod API yanıtında "status" alanını kontrol et
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Sadece geçerli bir istek alındıysa Redis'e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "customer_id": customer_id,
                    "company_name": company_name,
                    "status": "IN_PROGRESS",
                    "low_res_image_url": low_res_image_url,
                    "job_type": "customer_upscale",
                    "request_id": request_id
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your upscale request is being processed.')
            else:
                # İstek başarısız olduysa, kullanıcıya bildirim gönder ve işlemi durdur
                notify_status_update(room, 'failed', 'Your upscale request could not be processed.')
                logging.error(f"Upscale request for user {customer_id} failed with status: {result.get('status')}")
                return {"message": "Upscale request failed. Please try again later."}, 500

            return result


    # Text To Video

    @staticmethod
    def text_to_video(prompt, customer, room):
        """Kuyruğa göre video generation işlemini başlatır."""
        guid = str(uuid.uuid4())
        job = add_to_video_queue(
            EnterpriseService.run_text_to_video_generation,
            prompt=prompt, customer=customer, room=room, request_id=guid
        )
        notify_status_update(room, 'processing', 'Your video request is being processed.')
        return jsonify({"job_id": guid, "message": "Your request has been queued." })

    @staticmethod
    def run_text_to_video_generation(prompt, customer, request_id, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/T2V.json')

            # translatePrompt = VideoGenerationService.translatePrompt(prompt)

            """
            # workflow.json dosyasını güncelle
            updated_workflow = VideoGenerationService.update_workflow_with_t2v(
                path=workflow_path, prompt=translatePrompt,
            )
            """

            updated_workflow = VideoGenerationService.update_workflow_with_t2v(
                path=workflow_path, prompt=prompt,
            )

            customer_id = str(customer.id)
            company_name = customer.company_name

            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=customer_id, username=company_name,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_VIDEO_URL",
                timeout=600
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "customer_id": customer_id,
                    "company_name": company_name,
                    "prompt": prompt,
                    "room": room,
                    "status": "IN_PROGRESS",
                    "job_type": "customer_text_to_video",
                    "request_id": request_id
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your video request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your video generation request could not be processed.')
                logging.error(f"Video generation request for user {customer_id} failed with status: {result.get('status')}")
                return {"message": "Video generation request failed. Please try again later."}, 500

        return result

    # Image To Video

    @staticmethod
    def image_to_video(prompt, customer, image_bytes, room):
        """Kuyruğa göre video generation işlemini başlatır."""
        guid = str(uuid.uuid4())
        job = add_to_video_queue(
            EnterpriseService.run_image_to_video_generation,
            prompt=prompt, customer=customer, image_bytes=image_bytes, room=room, request_id=guid
        )
        notify_status_update(room, 'processing', 'Your video request is being processed.')
        return jsonify({"job_id": guid, "message": "Your request has been queued." })

    @staticmethod
    def run_image_to_video_generation(prompt, customer, image_bytes, request_id, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        customer_id = str(customer.id)
        company_name = customer.company_name

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/I2V.json')

            # translatePrompt = VideoGenerationService.translatePrompt(prompt)

            """
            # workflow.json dosyasını güncelle
            updated_workflow = VideoGenerationService.update_workflow_with_i2v(
                path=workflow_path, prompt=translatePrompt, image_bytes=image_bytes
            )
            """

            updated_workflow = VideoGenerationService.update_workflow_with_i2v(
                path=workflow_path, prompt=prompt, image_bytes=image_bytes
            )

            image_url = upload_image_to_s3(
                app=app, image_bytes=image_bytes, userid=customer_id, s3_folder_name="S3_FOLDER_VIDEO",
                file_extension="png"
            )

            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=customer_id, username=company_name,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_VIDEO_URL",
                timeout=600
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "customer_id": customer_id,
                    "company_name": company_name,
                    "prompt": prompt,
                    "room": room,
                    "status": "IN_PROGRESS",
                    "ref_image": image_url,
                    "job_type": "customer_image_to_video",
                    "request_id": request_id
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your video request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your video generation request could not be processed.')
                logging.error(f"Video generation request for user {customer_id} failed with status: {result.get('status')}")
                return {"message": "Video generation request failed. Please try again later."}, 500

        return result

    def save_request_to_db(self, customer_id, company_name, request_type, prompt, response, low_res_url,seed, model_type,
                           resolution, ref_image, request_id, consistent):
        """
        Saves a request to the database.
        """
        result = response.get("output", {}).get("message")
        if ".png" in result:
            result = result.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

        if ".mp4" in result:
            result = result.split(".mp4")[0] + ".mp4"  # Sadece .mp4'ye kadar olan kısmı al


        new_request = EnterpriseRequest(
            company_id=customer_id,
            company_name=company_name,
            request_type=request_type,
            prompt=prompt,
            low_res_url=low_res_url,
            image = result if result and '.png' in result else None,
            seed=seed,
            model_type=model_type or "normal",
            resolution=resolution or "1024x1024",
            created_at=datetime.datetime.utcnow(),
            ref_image=ref_image,
            video_url=result if result and '.mp4' in result else None,
            job_id=request_id,
            consistent = consistent
        )
        new_request.save()
        return new_request


    # Get All Fonksiyonları --------------------------------------------------------------------------------------------

    def get_all_text_to_images(self, customer):
        # Define the fields you want to include
        fields_to_include = [
            'id',
            'prompt',
            'image',
            'seed',
            'model_type',
            'resolution',
            'created_at',
            'webp_url'
        ]

        requests_list = self.get_company_requests(customer_id=str(customer.id), request_type="text-to-image", fields=fields_to_include)

        return requests_list

    def get_all_upscale_enhances(self, customer):
        # Define the fields you want to include
        fields_to_include = [
            'id',
            'image',
            'low_res_url',
            'created_at',
            'webp_url'
        ]

        requests_list = self.get_company_requests(
            customer_id=str(customer.id),
            request_type="upscale",
            fields=fields_to_include
        )

        return requests_list

    def get_all_text_to_video(self, customer):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'prompt',
            'video_url',
            'created_at',
        ]

        request = self.get_company_requests(
            customer_id=str(customer.id),
            request_type="text-to-video",
            fields=fields_to_include,
        )

        return request

    def get_all_image_to_video(self, customer):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'prompt',
            'ref_image',
            'video_url',
            'created_at',
        ]

        request = self.get_company_requests(
            customer_id=str(customer.id),
            request_type="image-to-video",
            fields=fields_to_include,
        )

        return request

    def get_company_requests(self, customer_id, request_type, fields):
        # Query the database for the specific requests
        requests = EnterpriseRequest.objects(
            company_id=str(customer_id),
            request_type=request_type
        ).only(*fields)

        # Convert the QuerySet to a list of dictionaries
        requests_list = []
        for req in requests:
            req_dict = {}
            for field in fields:
                value = getattr(req, field, None)
                if field == 'id':
                    # Convert ObjectId to string
                    req_dict['id'] = str(value)
                elif isinstance(value, datetime.datetime):
                    # Format datetime fields
                    req_dict[field] = value.isoformat()
                else:
                    req_dict[field] = value
            requests_list.append(req_dict)

        return requests_list

    # Get One Fonksiyonları --------------------------------------------------------------------------------------------

    def get_one_text_to_image(self, customer, request_id):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'prompt',
            'image',
            'seed',
            'model_type',
            'resolution',
            'created_at',
            'webp_url'
        ]

        request = self.get_company_request_by_id(
            customer_id=str(customer.id),
            request_type="text-to-image",
            fields=fields_to_include,
            request_id=request_id
        )

        return request

    def get_one_text_to_video(self, customer, request_id):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'prompt',
            'video_url',
            'created_at',
        ]

        request = self.get_company_request_by_id(
            customer_id=str(customer.id),
            request_type="text-to-video",
            fields=fields_to_include,
            request_id=request_id
        )

        return request

    def get_one_image_to_video(self, customer, request_id):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'prompt',
            'ref_image',
            'video_url',
            'created_at',
        ]

        request = self.get_company_request_by_id(
            customer_id=str(customer.id),
            request_type="image-to-video",
            fields=fields_to_include,
            request_id=request_id
        )

        return request

    def get_one_upscale_enhance(self, customer, request_id):
        # Dönmek istediğiniz alanları tanımlayın
        fields_to_include = [
            'id',
            'image',
            'low_res_url',
            'created_at',
            'webp_url'
        ]

        request = self.get_company_request_by_id(
            customer_id=str(customer.id),
            request_type="upscale",
            fields=fields_to_include,
            request_id=request_id
        )

        return request

    def get_company_request_by_id(self, customer_id, request_type, fields, request_id):
        # Veritabanından belirli isteği sorgulayın
        request = EnterpriseRequest.objects(
            company_id=customer_id,
            request_type=request_type,
            id=request_id
        ).only(*fields).first()

        if not request:
            return None  # Veya uygun bir hata mesajı döndürebilirsiniz

        # Sonucu sözlüğe dönüştürün
        req_dict = {}
        for field in fields:
            value = getattr(request, field, None)
            if field == 'id':
                # ObjectId'yi string'e çevirin
                req_dict['id'] = str(value)
            elif isinstance(value, datetime.datetime):
                # datetime alanlarını formatlayın
                req_dict[field] = value.isoformat()
            else:
                req_dict[field] = value
        return req_dict

    def get_query_job_id(self, customer, job_id):
        request = EnterpriseRequest.objects(job_id=job_id).first()

        if not request:
            return {"job_id":job_id, "message":"Your request has been queued."}

        return request
