import json
import os
import requests
from flask import current_app

class TextToImageService:
    @staticmethod
    def update_workflow_with_prompt(path, prompt):
        """
        Verilen path'e göre workflow.json dosyasını okuyup, prompt değerini günceller.
        """
        # workflow.json dosyasını oku
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["workflow"]["6"]["inputs"]["text"] = prompt

        return workflow_data

    @staticmethod
    def generate_image_from_text(prompt):
        # Proje dizininde yer alan workflow.json dosyasının yolu
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_dev.json')

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, prompt)

        # RunPod API endpoint URL'si
        runpod_url = current_app.config['RUNPOD_URL']

        # İstek başlıkları (headers)
        headers = {
            "Content-Type": "application/json",
            "Authorization": current_app.config['RUNPOD_API_KEY']
        }

        # RunPod API'sine POST isteği gönderme
        response = requests.post(runpod_url, json=updated_workflow, headers=headers)

        # Eğer istek başarılı olduysa yanıtı döndür
        if response.status_code == 200:
            return response.json()  # Yanıtı JSON olarak döndürün
        else:
            response.raise_for_status()  # Bir hata varsa hatayı fırlatın