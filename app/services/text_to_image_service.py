import json
import logging
import os
import requests
from app.models.image_request_model import ImageRequest
from app.services.base_service import BaseService
from requests.exceptions import Timeout, ConnectionError, RequestException

class TextToImageService(BaseService):
    model = ImageRequest

    @staticmethod
    def update_workflow_with_prompt(path, prompt):
        """
        workflow.json dosyasını okur ve verilen prompt ile günceller.
        """
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["workflow"]["6"]["inputs"]["text"] = prompt
        return workflow_data

    @staticmethod
    def generate_image_directly(app, prompt, payload):
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_dev.json')

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, prompt)
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
                user_id = payload["sub"]
                username = payload["username"]
                TextToImageService.save_request_to_db(user_id, username, prompt, message)

                return result  # Yanıtı JSON olarak döndür
            else:
                response.raise_for_status()  # Bir hata varsa hatayı fırlatın

    @staticmethod
    def save_request_to_db(user_id, username, prompt, message):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        image_request = ImageRequest(
            user_id=user_id,
            username=username,
            prompt=prompt,
            image=message
        )
        image_request.save()

    @staticmethod
    def get_requests_by_user_id(user_id):
        """
        Veritabanından kullanıcı ID'sine göre istekleri getirir.
        """
        return ImageRequest.objects(user_id=user_id).all()
