import base64
import json
import logging
import math
import os
from datetime import datetime

import openai

from app.models.image_to_image_model import ImageToImage
from app.services.base_service import BaseService
from app.services.video_generation_service import VideoGenerationService
from app.utils.convert_to_webp import upload_image_to_s3, process_and_save_image
from app.utils.notification import notify_status_update
from app.utils.queue_manager import add_to_upscale_queue, redis_conn
from app.utils.runpod_requets import send_runpod_request


openai.api_key = os.getenv("OPEN_AI_KEY")

class ImageToImageService(BaseService):
    model = ImageToImage
    Duty_Translate = "You are a translator GPT, your job is to translate the {prompt} from any language to English without any changes in the context. Be straightforward and direct for the translation"

    @staticmethod
    def translatePrompt(text):
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{ImageToImageService.Duty_Translate}"},
                {"role": "user", "content": f"prompt: {text}"}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content

    @staticmethod
    def update_workflow(path, image_btyes, prompt):
        """
        workflow.json dosyasını okur ve verilen image_bytes ile günceller.
        """
        # workflow.json dosyasını okuyalım
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # image_bytes'ı base64 formatına dönüştür
        image_base64 = base64.b64encode(image_btyes).decode('utf-8')
        translate_prompt = ImageToImageService.translatePrompt(prompt)

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["images"][0]["image"] = image_base64
        workflow_data["input"]["workflow"]["1"]["inputs"]["clip_l"] = translate_prompt
        workflow_data["input"]["workflow"]["1"]["inputs"]["t5xxl"] = translate_prompt

        return workflow_data

    @staticmethod
    def get_request_by_userid(user_id, page=1, per_page=8):
        """
        Verilen ID'ye göre kullanıcıya ait upscale taleplerini sayfalama ile getirir.
        """
        # Kullanıcıya ait toplam kayıt sayısını alıyoruz
        total_requests = ImageToImage.objects(user_id=user_id).count()

        # Toplam sayfa sayısını hesaplıyoruz
        total_pages = math.ceil(total_requests / per_page)

        # Sayfalama için skip miktarını hesaplıyoruz
        skip = (page - 1) * per_page

        # İlgili sayfaya göre upscale isteklerini alıyoruz
        requests = ImageToImage.objects(user_id=user_id).order_by('-datetime').skip(skip).limit(per_page)

        # Yeni bir liste oluşturup her öğeyi özelleştiriyoruz
        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "ref_image": request.ref_image,
                "image_url_webp": request.image_url_webp,
                "image": request.image,
                "prompt": request.prompt
            }
            custom_requests.append(custom_request)

        # Sonuçları döndürürken toplam sayfa ve toplam kayıt sayısını da ekliyoruz
        return {
            "requests": custom_requests,
            "total_requests": total_requests,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }

        # return custom_requests

    @staticmethod
    def add_to_image_to_image_queue(image_bytes, prompt, payload, room):
        """Kuyruğa göre upscale işlemini başlatır."""
        job = add_to_upscale_queue(
            ImageToImageService.run_image_to_image,
            image_bytes=image_bytes, prompt= prompt, payload=payload, room=room
        )
        notify_status_update(room, 'processing', 'Your request is being processed.')
        return job

    @staticmethod
    def run_image_to_image(image_bytes, prompt, payload, room=None):
        """I2I işlemini çalıştırır ve Redis'te takip eder."""
        from app import create_app
        app = create_app()

        with app.app_context():
            user_id = payload["sub"]
            username = payload["username"]

            workflow_path = os.path.join(os.getcwd(), 'app/workflows/I2I.json')
            updated_workflow = ImageToImageService.update_workflow(workflow_path, image_bytes, prompt)
            low_res_image_url = upload_image_to_s3(
                app=app, image_bytes=image_bytes, userid=user_id, s3_folder_name="S3_FOLDER_I2I_IMAGE",
                file_extension="png"
            )

            result, status_code = send_runpod_request(
                app=app, user_id=user_id, username=username, data=json.dumps(updated_workflow),
                runpod_url="RUNPOD_I2I_URL", timeout=600
            )

            # RunPod API yanıtında "status" alanını kontrol et
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Sadece geçerli bir istek alındıysa Redis'e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "user_id": user_id,
                    "username": username,
                    "status": "IN_PROGRESS",
                    "ref_image": low_res_image_url,
                    "job_type": "image_to_image_generation",
                    "prompt": prompt
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your I2I request is being processed.')
            else:
                # İstek başarısız olduysa, kullanıcıya bildirim gönder ve işlemi durdur
                notify_status_update(room, 'failed', 'Your upscale request could not be processed.')
                logging.error(f"I2I request for user {user_id} failed with status: {result.get('status')}")
                return {"message": "I2I request failed. Please try again later."}, 500

            return result

    @staticmethod
    def save_request_to_db(response, user_id, username, ref_image, prompt, app):
            """
            Kullanıcı isteğini veritabanına kaydeder.
            """

            execution_time = response.get("executionTime")
            result_image = response.get("output", {}).get("message")
            # '.png' ile biten kısmı yakalayıp sonrasını silme
            if ".png" in result_image:
                high_res_image = result_image.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

            webp_url = process_and_save_image(app, result_image, user_id)

            if execution_time is not None:
                cost = float(execution_time) * 0.00031 * 1e-3
            else:
                cost = 0.0  # veya başka bir varsayılan değer

            imagetoimage = ImageToImage(
                datetime=datetime.utcnow(),  # Şu anki tarih ve saat
                ref_image=ref_image,  # Düşük çözünürlüklü resim URL'si
                image=result_image,  # Yüksek çözünürlüklü resim URL'si
                image_url_webp=webp_url,
                cost=cost,  # Hesaplanan maliyet
                execution_time=float(execution_time) if execution_time else 0.0,  # İşlem süresi
                user_id=user_id,  # Kullanıcı ID'si (gerekirse)
                username=username,
                source="web",  # Kaynak bilgisi (örneğin Discord)
                prompt=prompt
            )
            imagetoimage.save()
