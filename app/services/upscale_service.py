# upscale_service.py
import base64
import os
import uuid
import json
import logging
import requests
from datetime import datetime

import boto3
from requests.exceptions import Timeout, ConnectionError, RequestException


from app.models.upscale_model import Upscale
from app.services.base_service import BaseService
from app.utils.runpod_requets import send_runpod_request
from app.utils.convert_to_webp import upload_image_to_s3, process_and_save_image


class UpscaleService(BaseService):
    model = Upscale
    """
    Bu sınıf, upscale işlemleriyle ilgili servis fonksiyonlarını barındıracak.
    """

    @staticmethod
    def create_upscale_request(app,low_res_image, payload):
        logging.info("upscale servis girildi")
        # Parametrelerin varlığını kontrol et
        if not low_res_image:
            raise ValueError("Low resolution image is required.")

        if not payload or 'sub' not in payload:
            raise ValueError("Payload is required and must contain user information.")

        user_id = payload["sub"]
        username = payload["username"]

        workflow_path = os.path.join(os.getcwd(), 'app/workflows/upscale_workflow.json')


        # workflow.json dosyasını güncelle
        updated_workflow = UpscaleService.update_workflow(workflow_path, low_res_image)

        result, status_code = send_runpod_request(app=app, user_id=user_id, username=username, data=json.dumps(updated_workflow), runpod_url="RUNPOD_UPSCALE_URL",timeout=600)
        print(f"runpod istek sonrası {result}")

        low_res_image_url = upload_image_to_s3(app=app, image_bytes=low_res_image,
                                                              userid=user_id, s3_folder_name="S3_FOLDER_UPSCALE_IMAGE", file_extension="png")
        print("deneme")
        UpscaleService.save_request_to_db(response=result, user_id=user_id, username=username,
                                          low_res_image=low_res_image_url, app=app)
        return result


    @staticmethod
    def get_upscale_request_by_userid(user_id, page=1, per_page=8):
        """
        Verilen ID'ye göre bir upscale talebini getirir.
        """
        skip = (page - 1) * per_page
        requests =  Upscale.objects(user_id=user_id).order_by('-datetime').skip(
            skip).limit(per_page)

        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "low_res_image_url": request.low_res_image_url,
                "high_res_image_url": request.image_url_webp,
                "high_image_png": request.high_res_image_url,
            }
            custom_requests.append(custom_request)

        return custom_requests

    @staticmethod
    def get_all_upscale_requests():
        """
        Tüm upscale taleplerini getirir.
        """
        return Upscale.objects().all()

    @staticmethod
    def update_workflow(path, image_btyes):
        """
        workflow.json dosyasını okur ve verilen image_bytes ile günceller.
        """
        # workflow.json dosyasını okuyalım
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # image_bytes'ı base64 formatına dönüştür
        image_base64 = base64.b64encode(image_btyes).decode('utf-8')

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["images"][0]["image"] = image_base64

        return workflow_data

    @staticmethod
    def save_request_to_db(response, user_id,username, low_res_image, app):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """

        execution_time = response.get("executionTime")
        high_res_image = response.get("output", {}).get("message")
        # '.png' ile biten kısmı yakalayıp sonrasını silme
        if ".png" in high_res_image:
            high_res_image = high_res_image.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

        webp_url = process_and_save_image(app, high_res_image, user_id)

        if execution_time is not None:
            cost = float(execution_time) * 0.00031 * 1e-3
        else:
            cost = 0.0  # veya başka bir varsayılan değer

        upscale = Upscale(
            datetime=datetime.utcnow(),  # Şu anki tarih ve saat
            low_res_image_url=low_res_image,  # Düşük çözünürlüklü resim URL'si
            high_res_image_url=high_res_image,  # Yüksek çözünürlüklü resim URL'si
            image_url_webp=webp_url,
            cost=cost,  # Hesaplanan maliyet
            execution_time=float(execution_time) if execution_time else 0.0,  # İşlem süresi
            user_id=user_id,  # Kullanıcı ID'si (gerekirse)
            username=username,
            source="web"  # Kaynak bilgisi (örneğin Discord)
        )
        upscale.save()

