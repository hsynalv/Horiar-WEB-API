import json
import logging
import os
import datetime

from app.models.enterprise.enterprise_customer_model import EnterpriseCustomer
from app.models.enterprise.enterprise_request_model import EnterpriseRequest
from app.services.base_service import BaseService
import secrets

from app.services.text_to_image_service import TextToImageService
from app.services.upscale_service import UpscaleService
from app.utils.notification import notify_status_update
from app.utils.queue_manager import add_to_image_queue, redis_conn
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

    def text_to_image(prompt, model_type, resolution, customer, prompt_fix, consistent, room):
        """Kuyruğa göre image generation işlemini başlatır."""
        job = add_to_image_queue(
            EnterpriseService.run_image_generation,
            prompt=prompt, model_type=model_type, resolution=resolution, customer=customer, prompt_fix=prompt_fix,
            room=room, consistent=consistent  # room parametresi yalnızca **kwargs olarak geçiliyor
        )
        notify_status_update(room, 'processing', 'Your request is being processed.')
        return job

    def run_image_generation(prompt, model_type, resolution, customer, prompt_fix, consistent, room=None):
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
                    "room": room,
                    "status": "IN_PROGRESS",
                    "prompt_fix": prompt_fix,
                    "consistent": consistent,
                    "job_type": "customer_image_generation",
                    "customer": customer
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your image generation request could not be processed.')
                logging.error(f"(Enterprise)Image generation request for user {str(customer.id)} failed with status: {result.get('status')}")
                return {"message": "Image generation request failed. Please try again later."}, 500

        return result



    def upscale_enhance(self, app, low_res_image, customer):
        # Parametrelerin varlığını kontrol et
        if not low_res_image:
            raise ValueError("Low resolution image is required.")

        workflow_path = os.path.join(os.getcwd(), 'app/workflows/upscale_workflow.json')

        # workflow.json dosyasını güncelle
        updated_workflow = UpscaleService.update_workflow(workflow_path, low_res_image)

        result, status_code = send_runpod_request(app=app, user_id=str(customer.id),
                                                  username=f"Enterprise: {customer.company_name}",
                                                  data=json.dumps(updated_workflow), runpod_url="RUNPOD_UPSCALE_URL",
                                                  timeout=600)

        low_res_image_url = upload_image_to_s3(app=app, image_bytes=low_res_image,
                                                                      userid=str(customer.id), s3_folder_name="S3_FOLDER_UPSCALE_IMAGE", file_extension="png")

        self.save_request_to_db(customer_id=str(customer.id), company_name=customer.company_name, request_type="upscale",
                                prompt=None, response=result, low_res_url=low_res_image_url, seed=None, model_type=None,
                                resolution=None, app=app)
        return {
            "result": result,
            "low_res_image_url": low_res_image_url
        }


    def save_request_to_db(self, customer_id, company_name, request_type, prompt, response, low_res_url,seed, model_type, resolution, app):
        """
        Saves a request to the database.
        """
        result = response.get("output", {}).get("message")
        if ".png" in result:
            result = result.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

        webp_url = None
        if result:
            webp_url = process_and_save_image(app, result, customer_id)

        new_request = EnterpriseRequest(
            company_id=customer_id,
            company_name=company_name,
            request_type=request_type,
            prompt=prompt,
            low_res_url=low_res_url,
            image=result,
            webp_url=webp_url,
            seed=seed,
            model_type=model_type or "normal",
            resolution=resolution or "1024x1024",
            created_at=datetime.datetime.utcnow()
        )
        new_request.save()
        return new_request


    # Get Fonksiyonları ----------------------------------------------------------------------------------------------------------------------

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

    def get_all_text_to_images_consistent(self, customer):
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

        requests_list = self.get_company_requests(customer_id=str(customer.id), request_type="text-to-image-consistent",
                                                  fields=fields_to_include)

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

    def get_one_text_to_image_consistent(self, customer, request_id):
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
            request_type="text-to-image-consistent",
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
