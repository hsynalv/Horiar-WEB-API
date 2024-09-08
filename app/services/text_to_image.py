import json
import os
import requests
from queue import Queue

from app.models.image_request_model import ImageRequest


class TextToImageService:
    @staticmethod
    def update_workflow_with_prompt(path, prompt):
        # workflow.json dosyasını oku
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["workflow"]["6"]["inputs"]["text"] = prompt

        return workflow_data

    @staticmethod
    def generate_image_directly(app, prompt, payload):
        """
        Kuyruk kullanmadan doğrudan RunPod API'sine istek göndererek prompt'a göre görüntü oluşturur.
        """
        # Proje dizininde yer alan workflow.json dosyasının yolu
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_dev.json')

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, prompt)

        # Uygulama bağlamı içinde ayarları çek
        with app.app_context():
            runpod_url = app.config['RUNPOD_URL']
            headers = {
                "Content-Type": "application/json",
                "Authorization": app.config['RUNPOD_API_KEY']
            }

            # RunPod API'sine POST isteği gönderme
            response = requests.post(runpod_url, json=updated_workflow, headers=headers)

            # Eğer istek başarılı olduysa yanıtı döndür
            if response.status_code == 200:
                result = response.json()
                # RunPod API yanıtından message bilgisini al
                message = result.get("output", {}).get("message")

                # RunPod API isteği başarılı olduğunda kaydetme işlemini yapıyoruz
                user_id = payload["sub"]
                username = payload["username"]
                TextToImageService.save_request_to_db(app, user_id, username, prompt, message)

                return result  # Yanıtı JSON olarak döndür
            else:
                response.raise_for_status()  # Bir hata varsa hatayı fırlatın

    @staticmethod
    def save_request_to_db(app, user_id, username, prompt, message):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        with app.app_context():
            requests_collection = app.db["image_requests"]
            image_request = ImageRequest(
                user_id=user_id,
                username=username,
                prompt=prompt,
                image=message
            )
            requests_collection.insert_one(image_request.to_dict())

    @staticmethod
    def get_requests_by_user_id(app, payload):
        """
        Veritabanından kullanıcı ID'sine göre istekleri getirir.
        """
        with app.app_context():
            # Veritabanı bağlantısını al
            requests_collection = app.db["image_requests"]
            user_id = payload["sub"]

            # Kullanıcı ID'sine göre sorgu yap
            results = requests_collection.find({"user_id": user_id})

            # Sonuçları liste halinde döndür
            return [ImageRequest.from_dict(result) for result in results]
