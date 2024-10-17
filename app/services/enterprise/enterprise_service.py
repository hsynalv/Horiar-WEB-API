import json
import logging
import os
import requests
import datetime
from requests.exceptions import Timeout, ConnectionError, RequestException

from flask import current_app
from app.models.enterprise.enterprise_customer_model import EnterpriseCustomer
from app.models.enterprise.enterprise_request_model import EnterpriseRequest
from app.services.base_service import BaseService
import secrets

from app.services.text_to_image_service import TextToImageService
from app.services.upscale_service import UpscaleService


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

    def text_to_image(self, app, prompt, model_type, resolution, customer):
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_promptfix.json')

        """
        nsfw_flag = openai.moderations.create(input=prompt).results[0].flagged
        if nsfw_flag:
            return jsonify({"warning: This prompt violates our safety policy"}), 404
        """
        newPrompts = TextToImageService.promptEnhance(prompt)

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, newPrompts, model_type,
                                                                          resolution, True)
        seed = updated_workflow["input"]["workflow"]["112"]["inputs"]["noise_seed"]
        # Uygulama bağlamı içinde ayarları çek
        with app.app_context():
            runpod_url = app.config['RUNPOD_URL']
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['RUNPOD_API_KEY']}",
            }

            try:
                # RunPod API'sine POST isteği gönderme
                response = requests.post(runpod_url, headers=headers, data=json.dumps(updated_workflow), timeout=60)
            except Timeout:
                logging.error("RunPod isteği zaman aşımına uğradı!")
                return {"message": "RunPod isteği zaman aşımına uğradı."}, 500
            except ConnectionError:
                logging.error("RunPod bağlantı hatası!")
                return {"message": "RunPod bağlantı hatası."}, 500
            except RequestException as e:
                logging.error(f"RunPod isteğinde bir hata oluştu: {str(e)}")
                return {"message": f"RunPod isteğinde bir hata oluştu: {str(e)}"}, 500

            # Eğer istek başarılı olduysa yanıtı döndür
            if response.status_code == 200:
                result = response.json()
                message = result.get("output", {}).get("message")

                # API yanıtını veritabanına kaydet
                self.save_request_to_db(customer_id=str(customer.id), company_name=customer.company_name, request_type="text-to-image",
                                        prompt=prompt, result=str(message), low_res_url=None, seed=str(seed),
                                        model_type=model_type, resolution=resolution)
                return result  # Yanıtı JSON olarak döndür
            else:
                response.raise_for_status()

    def text_to_image_consistent(self, app, prompt, model_type, resolution, customer):
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_promptfix.json')

        """
        nsfw_flag = openai.moderations.create(input=prompt).results[0].flagged
        if nsfw_flag:
            return jsonify({"warning: This prompt violates our safety policy"}), 404
        """
        newPrompts = TextToImageService.promptEnhance(prompt)

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, newPrompts, model_type,
                                                                          resolution, False)
        seed = updated_workflow["input"]["workflow"]["112"]["inputs"]["noise_seed"]
        # Uygulama bağlamı içinde ayarları çek
        with app.app_context():
            runpod_url = app.config['RUNPOD_URL']
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['RUNPOD_API_KEY']}",
            }

            try:
                # RunPod API'sine POST isteği gönderme
                response = requests.post(runpod_url, headers=headers, data=json.dumps(updated_workflow), timeout=60)
            except Timeout:
                logging.error("RunPod isteği zaman aşımına uğradı!")
                return {"message": "RunPod isteği zaman aşımına uğradı."}, 500
            except ConnectionError:
                logging.error("RunPod bağlantı hatası!")
                return {"message": "RunPod bağlantı hatası."}, 500
            except RequestException as e:
                logging.error(f"RunPod isteğinde bir hata oluştu: {str(e)}")
                return {"message": f"RunPod isteğinde bir hata oluştu: {str(e)}"}, 500

            # Eğer istek başarılı olduysa yanıtı döndür
            if response.status_code == 200:
                result = response.json()
                message = result.get("output", {}).get("message")
                # API yanıtını veritabanına kaydet
                self.save_request_to_db(customer_id=str(customer.id), company_name=customer.company_name, request_type="text-to-image-consistent",
                                        prompt=prompt, result=message, low_res_url=None, seed=str(seed), model_type=model_type, resolution=resolution)
                return result  # Yanıtı JSON olarak döndür
            else:
                response.raise_for_status()  # Bi

    def upscale_enhance(self, app, low_res_image, customer):
        # Parametrelerin varlığını kontrol et
        if not low_res_image:
            raise ValueError("Low resolution image is required.")

        workflow_path = os.path.join(os.getcwd(), 'app/workflows/upscale_workflow.json')

        # workflow.json dosyasını güncelle
        updated_workflow = UpscaleService.update_workflow(workflow_path, low_res_image)

        with app.app_context():
            runpod_url = app.config['RUNPOD_UPSCALE_URL']
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {app.config['RUNPOD_API_KEY']}",
            }
            print("runpod istek atıldı")

            try:
                # RunPod API'sine POST isteği gönderme
                response = requests.post(runpod_url, headers=headers, data=json.dumps(updated_workflow), timeout=600)
            except Timeout:
                logging.error("RunPod isteği zaman aşımına uğradı!")
                return {"message": "RunPod isteği zaman aşımına uğradı."}, 500
            except ConnectionError:
                logging.error("RunPod bağlantı hatası!")
                return {"message": "RunPod bağlantı hatası."}, 500
            except RequestException as e:
                logging.error(f"RunPod isteğinde bir hata oluştu: {str(e)}")
                return {"message": f"RunPod isteğinde bir hata oluştu: {str(e)}"}, 500

            # Eğer istek başarılı olduysa yanıtı döndür
            if response.status_code == 200:
                result = response.json()
                message = result.get("output", {}).get("message")

                # S3'e yükleme işlemi
                try:
                    low_res_image_url = UpscaleService.upload_image_to_s3(app=app, image_bytes=low_res_image,
                                                                          userid=str(customer.id))
                except Exception as e:
                    raise Exception(f"Failed to upload image to S3: {str(e)}")

                # API yanıtını veritabanına kaydet
                self.save_request_to_db(customer_id=str(customer.id), company_name=customer.company_name, request_type="upscale",
                                        prompt=None, result=message, low_res_url=low_res_image_url,seed=None, model_type=None,
                                        resolution=None)

                return {
                    "result": result,
                    "low_res_image_url": low_res_image_url
                }
            else:
                response.raise_for_status()

    def save_request_to_db(self, customer_id, company_name, request_type, prompt, result, low_res_url,seed, model_type, resolution):
        """
        Saves a request to the database.
        """
        if ".png" in result:
            result = result.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

        new_request = EnterpriseRequest(
            company_id=customer_id,
            company_name=company_name,
            request_type=request_type,
            prompt=prompt,
            low_res_url=low_res_url,
            image=result,
            seed=seed,
            model_type=model_type or "normal",
            resolution=resolution or "1024x1024",
            created_at=datetime.datetime.utcnow()
        )
        new_request.save()
        return new_request

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
