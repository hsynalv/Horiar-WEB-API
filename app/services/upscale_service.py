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

        low_res_image_url = UpscaleService.upload_image_to_s3(app=app, image_bytes=low_res_image,
                                                              userid=user_id)
        UpscaleService.save_request_to_db(response=result, user_id=user_id, username=username,
                                          low_res_image=low_res_image_url)
        return result


    @staticmethod
    def get_upscale_request_by_userid(user_id):
        """
        Verilen ID'ye göre bir upscale talebini getirir.
        """
        return Upscale.objects(user_id=user_id).order_by('-date').all()

    @staticmethod
    def get_all_upscale_requests():
        """
        Tüm upscale taleplerini getirir.
        """
        return Upscale.objects().all()

    @staticmethod
    def upload_image_to_s3(app, image_bytes, userid):
        """
        Verilen resim dosyasını Amazon S3'e yükler.

        :param image_bytes: Yüklenmesi gereken resim dosyasının binary verisi
        :return: Yüklenen dosyanın S3 URL'si
        """
        S3_BUCKET_NAME = app.config['S3_BUCKET_NAME']
        s3_folder = app.config['S3_FOLDER']
        aws_access_key = app.config['AWS_ACCESS_KEY_ID']
        aws_secret_key = app.config['AWS_SECRET_ACCESS_KEY']

        # S3'e erişmek için boto3'ün S3 client'ını oluşturuyoruz
        s3 = boto3.client('s3',
                          aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key)

        # Benzersiz bir dosya adı oluşturuyoruz (UUID kullanarak)
        file_extension = "png"  # Resmin uzantısını belirtin, gerekiyorsa değiştirilebilir
        file_name = f"{userid}-{uuid.uuid4()}.{file_extension}"

        # S3 bucket içine dosyanın tam yolu
        s3_key = os.path.join(s3_folder, file_name)

        try:
            # S3'e dosyayı yüklüyoruz
            s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=image_bytes, ContentType='image/png')

            # Yüklenen dosyanın S3 URL'sini oluşturuyoruz
            s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

            return s3_url
        except Exception as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")

    @staticmethod
    def update_workflow(path, image_bytes):
        """
        workflow.json dosyasını okur ve verilen image_bytes ile günceller.
        """
        # workflow.json dosyasını okuyalım
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # image_bytes'ı base64 formatına dönüştür
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # JSON verisinde gerekli değişiklikleri yap
        workflow_data["input"]["images"][0]["image"] = image_base64

        return workflow_data

    @staticmethod
    def save_request_to_db(response, user_id,username, low_res_image):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """

        execution_time = response.get("executionTime")
        high_res_image = response.get("output", {}).get("message")
        # '.png' ile biten kısmı yakalayıp sonrasını silme
        if ".png" in high_res_image:
            high_res_image = high_res_image.split(".png")[0] + ".png"  # Sadece .png'ye kadar olan kısmı al

        if execution_time is not None:
            cost = float(execution_time) * 0.00031 * 1e-3
        else:
            cost = 0.0  # veya başka bir varsayılan değer

        upscale = Upscale(
            datetime=datetime.utcnow(),  # Şu anki tarih ve saat
            low_res_image_url=low_res_image,  # Düşük çözünürlüklü resim URL'si
            high_res_image_url=high_res_image,  # Yüksek çözünürlüklü resim URL'si
            cost=cost,  # Hesaplanan maliyet
            execution_time=float(execution_time) if execution_time else 0.0,  # İşlem süresi
            user_id=user_id,  # Kullanıcı ID'si (gerekirse)
            username=username,
            source="web"  # Kaynak bilgisi (örneğin Discord)
        )
        upscale.save()

