from flask import jsonify
import json
import logging
import os
import requests
import openai
import random

from app.models.dataset_model import Dataset
from app.models.image_request_model import ImageRequest
from app.services.base_service import BaseService
from requests.exceptions import Timeout, ConnectionError, RequestException
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPEN_AI_KEY")

class TextToImageService(BaseService):
    model = None
    Duty = """
        Your job is to create a prompt according to the given clip model and inputs:
            1-) First Translate the prompt to English if needed. Do not send anything and go to step 2.
            2a-) If the given model is clip_l: Your job is to extract traits from translated prompt objects and create a new prompt by converting each trait to lowercase and separating them with commas and paying particular attention to styling prompts. Do not hallucinate and only type what is in the prompt.This prompt will be used for clip_l which is for stable diffusion. Just type the answer.
            2b-) If the given model is t5xxl: Your task is to refine the given prompt. Avoid introducing new details (hallucinating). Focus on correcting and enhancing the existing prompt, cover all the objects from the original prompt and do not miss anything. paying particular attention to styling prompts. The prompt will be used with the t5xxl model which is closer to natural language. Just type the answer.
        """

    @staticmethod
    def update_workflow_with_prompt(path, prompt):
        """
        workflow.json dosyasını okur ve verilen prompt ile günceller.
        """
        with open(path, 'r') as file:
            workflow_data = json.load(file)


        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["workflow"]["61"]["inputs"]["clip_l"] = prompt[0]
        workflow_data["input"]["workflow"]["61"]["inputs"]["t5xxl"] = prompt[1]
        workflow_data["input"]["workflow"]["112"]["inputs"]["noise_seed"] = random.randint(10**14, 10**15 - 1)
        logging.warning(workflow_data["input"]["workflow"]["112"]["inputs"]["noise_seed"])
        return workflow_data

    @staticmethod
    def generate_image_directly(app, prompt, payload):
        workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_promptfix.json')

        nsfw_flag = openai.moderations.create(input=prompt).results[0].flagged
        if nsfw_flag:
            return jsonify({"warning: This prompt violates our safety policy"}), 404

        newPrompts = TextToImageService.promptEnhance(prompt)

        # workflow.json dosyasını güncelle
        updated_workflow = TextToImageService.update_workflow_with_prompt(workflow_path, newPrompts)
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
        TextToImageService.model=ImageRequest
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

    def promptEnhance(input_text):
        clips = ["clip_l", "t5xxl"]
        prompts = []

        for clip in clips:
            response = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system",
                     "content": f"You are a helpful assistant. Your job is to apply {TextToImageService.Duty} according to {clip}."},
                    {"role": "user", "content": input_text}
                ]
            )

            prompt = response.choices[0].message.content
            prompts.append(prompt)

        TextToImageService.save_dataset_to_db(input_text, prompts)
        return prompts

    @staticmethod
    def save_dataset_to_db(mainPrompt, promptsFromAI):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        TextToImageService.model = Dataset
        dataset = Dataset(
            main_prompt=mainPrompt,
            clip_l=promptsFromAI[0],
            t5xxl=promptsFromAI[1],
        )

        dataset.save()


