import json
import os
import requests
import threading
from flask import current_app, jsonify
from queue import Queue
import time

from app.models.image_request_model import ImageRequest

# FIFO Kuyruğu
image_queue = Queue()
is_processing = False


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
    def generate_image_from_text(app, prompt):
        """
        RunPod API'sine istek göndererek prompt'a göre görüntü oluşturur.
        """
        # Proje dizininde yer alan workflow.json dosyasının yolu
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_dev.json')

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, prompt)

        # Uygulama bağlamı içinde ayarları çek
        with app.app_context():
            # RunPod API endpoint URL'si
            runpod_url = app.config['RUNPOD_URL']

            # İstek başlıkları (headers)
            headers = {
                "Content-Type": "application/json",
                "Authorization": app.config['RUNPOD_API_KEY']
            }

            # RunPod API'sine POST isteği gönderme
            response = requests.post(runpod_url, json=updated_workflow, headers=headers)

            # Eğer istek başarılı olduysa yanıtı döndür
            if response.status_code == 200:
                return response.json()  # Yanıtı JSON olarak döndürün
            else:
                response.raise_for_status()  # Bir hata varsa hatayı fırlatın

    @staticmethod
    def add_to_queue(app, prompt):
        if not prompt.strip():  # Boş veya yalnızca boşluklardan oluşan prompt
            raise ValueError("Prompt cannot be empty.")

        global is_processing
        result_queue = Queue()
        image_queue.put((app, prompt, result_queue))

        # Eğer işlem yapılmıyorsa kuyruğu işlemeye başla
        if not is_processing:
            threading.Thread(target=TextToImageService.process_queue).start()

        # Kuyrukta işlenen sonucun yanıtını bekler
        return result_queue.get()

    @staticmethod
    def process_queue():
        """
        Kuyruğa eklenen her isteği sırayla işler.
        """
        global is_processing
        is_processing = True

        while not image_queue.empty():
            app, prompt, result_queue = image_queue.get()

            # İstek işlenirken 2 saniyelik gecikme simülasyonu
            time.sleep(2)

            # Görsel oluşturma işlemi
            result = TextToImageService.generate_image_from_text(app, prompt)
            print(f"Processed: {prompt}")
            result_queue.put(result)  # Sonucu kuyrukta bekleyen işleme ilet

        is_processing = False

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

                # RunPod API isteği başarılı olduğunda kaydetme işlemini yapıyoruz
                user_id = payload["sub"]
                username = payload["username"]
                TextToImageService.save_request_to_db(app, user_id, username, prompt)

                return result  # Yanıtı JSON olarak döndür
            else:
                response.raise_for_status()  # Bir hata varsa hatayı fırlatın

    @staticmethod
    def save_request_to_db(app, user_id, username, prompt):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        with app.app_context():
            requests_collection = app.db["image_requests"]
            image_request = ImageRequest(
                user_id=user_id,
                username=username,
                prompt=prompt
            )
            requests_collection.insert_one(image_request.to_dict())