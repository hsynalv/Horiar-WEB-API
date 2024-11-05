import base64
import logging
import math
from datetime import datetime
import json
import os

import openai

from app.models.image_to_video_model import ImageToVideo
from app.models.text_to_video_model import TextToVideoGeneration
from app.services.base_service import BaseService
from app.utils.convert_to_webp import upload_image_to_s3
from app.utils.notification import notify_status_update
from app.utils.queue_manager import add_to_video_queue, redis_conn
from app.utils.runpod_requets import send_runpod_request

openai.api_key = os.getenv("OPEN_AI_KEY")

class VideoGenerationService(BaseService):
    model = None
    Duty_Translate = "You are a translator GPT, your job is to translate the {prompt} from any language to English without any changes in the context. Be straightforward and direct for the translation"



    @staticmethod
    def translatePrompt(text):
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{VideoGenerationService.Duty_Translate}"},
                {"role": "user", "content": f"prompt: {text}"}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content

    @staticmethod
    def promptEnhance(text):

        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{VideoGenerationService.Duty_Translate}"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        var = response.choices[0].message.content

        return var


    # ----------------------------------------- Text To Video --------------------------------------------------------

    @staticmethod
    def update_workflow_with_t2v(path, prompt):
        """
        workflow.json dosyasını okur ve verilen prompt ile günceller.
        """
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap

        workflow_data["input"]["workflow"]["30"]["inputs"]["prompt"] = prompt

        return workflow_data

    @staticmethod
    def save_text_to_video_to_db(user_id, username, prompt, response):
        """
        Kullanıcı video üretim isteğini veritabanına kaydeder.
        """
        # RunPod API'sinden gelen yanıt üzerinden işlem süresi ve maliyet hesaplaması
        execution_time = response.get("executionTime")
        if execution_time is not None:
            cost = float(execution_time) * 0.00151 * 1e-3
        else:
            cost = 0.0

        # Video URL'yi yanıtın "output" alanından al
        video_url = response.get("output", {}).get("message")
        if ".mp4" in video_url:
            video_url = video_url.split(".mp4")[0] + ".mp4"

        # TextToVideo kaydı
        text_to_video_record = TextToVideoGeneration(
            datetime=datetime.utcnow(),
            prompt=prompt,
            video_url=video_url,
            cost=cost,
            execution_time=float(execution_time) if execution_time else 0.0,
            user_id=user_id,
            username=username
        )

        # Veritabanına kaydet
        text_to_video_record.save()

        return text_to_video_record

    @staticmethod
    def get_text_to_video_by_user_id(user_id, page=1, per_page=4):
        """
        Veritabanından kullanıcı ID'sine göre video üretim isteklerini sayfalama ile getirir.
        """
        # Kullanıcıya ait toplam video isteği sayısını alıyoruz
        total_requests = TextToVideoGeneration.objects(user_id=user_id).count()

        # Toplam sayfa sayısını hesaplıyoruz
        total_pages = math.ceil(total_requests / per_page)

        # Sayfalama için skip miktarını hesaplıyoruz
        skip = (page - 1) * per_page

        # İlgili sayfaya göre istekleri alıyoruz
        requests = TextToVideoGeneration.objects(user_id=user_id).order_by('-datetime').skip(skip).limit(per_page)

        # Yeni bir liste oluşturup her öğeyi özelleştiriyoruz
        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "prompt": request.prompt,
                "video_url": request.video_url,
                "execution_time": request.execution_time,
                "cost": request.cost,
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

    def generate_text_to_video_with_queue(prompt, payload, room):
        """Kuyruğa göre video generation işlemini başlatır."""
        job = add_to_video_queue(
            VideoGenerationService.run_text_to_video_generation,
            prompt=prompt, payload=payload, room=room
        )
        notify_status_update(room, 'processing', 'Your video request is being processed.')
        return job

    @staticmethod
    def run_text_to_video_generation(prompt, payload, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/T2V.json')

            translatePrompt = VideoGenerationService.translatePrompt(prompt)

            # workflow.json dosyasını güncelle
            updated_workflow = VideoGenerationService.update_workflow_with_t2v(
                path=workflow_path, prompt=translatePrompt,
            )

            user_id = payload["sub"]
            username = payload["username"]

            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=user_id, username=username,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_VIDEO_URL",
                timeout=600
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "user_id": user_id,
                    "username": username,
                    "prompt": prompt,
                    "room": room,
                    "status": "IN_PROGRESS",
                    "job_type": "text_to_video_generation"
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your video request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your video generation request could not be processed.')
                logging.error(f"Video generation request for user {user_id} failed with status: {result.get('status')}")
                return {"message": "Video generation request failed. Please try again later."}, 500

        return result


    # ----------------------------------------- Image To Video --------------------------------------------------------

    @staticmethod
    def update_workflow_with_i2v(path, prompt, image_bytes):
        """
        workflow.json dosyasını okur ve verilen prompt ile günceller.
        """

        # image_bytes'ı base64 formatına dönüştür
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap

        workflow_data["input"]["workflow"]["30"]["inputs"]["prompt"] = prompt
        workflow_data["input"]["images"][0]["image"] = image_base64
        return workflow_data
    @staticmethod
    def save_image_to_video_to_db(user_id, username, prompt, image_url, response):
        """
        Kullanıcı video üretim isteğini veritabanına kaydeder.
        """
        # RunPod API'sinden gelen yanıt üzerinden işlem süresi ve maliyet hesaplaması
        execution_time = response.get("executionTime")
        if execution_time is not None:
            cost = float(execution_time) * 0.00151 * 1e-3
        else:
            cost = 0.0

        # Video URL'yi yanıtın "output" alanından al
        video_url = response.get("output", {}).get("message")
        if ".mp4" in video_url:
            video_url = video_url.split(".mp4")[0] + ".mp4"

        # ImageToVideo kaydı
        image_to_video_record = ImageToVideo(
            datetime=datetime.utcnow(),
            prompt=prompt,
            video_url=video_url,
            image_url=image_url,
            cost=cost,
            execution_time=float(execution_time) if execution_time else 0.0,
            user_id=user_id,
            username=username
        )

        # Veritabanına kaydet
        image_to_video_record.save()

        return image_to_video_record

    def generate_image_to_video_with_queue(prompt, payload, image_bytes, room):
        """Kuyruğa göre video generation işlemini başlatır."""
        job = add_to_video_queue(
            VideoGenerationService.run_image_to_video_generation,
            prompt=prompt, payload=payload, image_bytes=image_bytes, room=room
        )
        notify_status_update(room, 'processing', 'Your video request is being processed.')
        return job

    @staticmethod
    def run_image_to_video_generation(prompt, payload, image_bytes, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        user_id = payload["sub"]
        username = payload["username"]

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/I2V.json')

            translatePrompt = VideoGenerationService.translatePrompt(prompt)

            # workflow.json dosyasını güncelle
            updated_workflow = VideoGenerationService.update_workflow_with_i2v(
                path=workflow_path, prompt=translatePrompt, image_bytes=image_bytes
            )

            image_url = upload_image_to_s3(
                app=app, image_bytes=image_bytes, userid=user_id, s3_folder_name="S3_FOLDER_VIDEO",
                file_extension="png"
            )

            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=user_id, username=username,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_VIDEO_URL",
                timeout=600
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "user_id": user_id,
                    "username": username,
                    "prompt": prompt,
                    "room": room,
                    "status": "IN_PROGRESS",
                    "image_url": image_url,
                    "job_type": "image_to_video_generation"
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your video request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your video generation request could not be processed.')
                logging.error(f"Video generation request for user {user_id} failed with status: {result.get('status')}")
                return {"message": "Video generation request failed. Please try again later."}, 500

        return result

    @staticmethod
    def get_image_to_video_by_user_id(user_id, page=1, per_page=4):
        """
        Veritabanından kullanıcı ID'sine göre video üretim isteklerini sayfalama ile getirir.
        """
        # Kullanıcıya ait toplam video isteği sayısını alıyoruz
        total_requests = ImageToVideo.objects(user_id=user_id).count()

        # Toplam sayfa sayısını hesaplıyoruz
        total_pages = math.ceil(total_requests / per_page)

        # Sayfalama için skip miktarını hesaplıyoruz
        skip = (page - 1) * per_page

        # İlgili sayfaya göre istekleri alıyoruz
        requests = ImageToVideo.objects(user_id=user_id).order_by('-datetime').skip(skip).limit(per_page)

        # Yeni bir liste oluşturup her öğeyi özelleştiriyoruz
        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "prompt": request.prompt,
                "video_url": request.video_url,
                "image_url": request.image_url,
                "execution_time": request.execution_time,
                "cost": request.cost,
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