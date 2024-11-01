import json
import logging
import redis
import requests
from requests import Timeout, RequestException

from app.utils.queue_manager import redis_conn

# Özel logger'ı alıyoruz
runpod_logger = logging.getLogger("runpod")

def send_runpod_request(app, data, runpod_url, user_id, username, timeout=360):
    if not data:
        return {"message": "No data provided for RunPod request."}, 400

    with app.app_context():
        runpod_url = app.config[runpod_url]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {app.config['RUNPOD_API_KEY']}",
        }

    try:
        # RunPod API'sine POST isteği gönderme
        response = requests.post(runpod_url, headers=headers, data=data, timeout=timeout)

        # İsteğe ait yanıtı JSON formatında döndürme
        return response.json(), response.status_code

    except Timeout:
        runpod_logger.warning("---------------------------------------------------------------------------------")
        runpod_logger.error(f"RunPod isteği zaman aşımına uğradı! -- user_id: {user_id} - username: {username}")
        runpod_logger.warning("---------------------------------------------------------------------------------")
        return {"message": "RunPod isteği zaman aşımına uğradı."}, 500

    except ConnectionError:
        runpod_logger.warning("---------------------------------------------------------------------------------")
        runpod_logger.error("RunPod bağlantı hatası! -- user_id: {user_id} - username: {username}")
        runpod_logger.warning("---------------------------------------------------------------------------------")
        return {"message": "RunPod bağlantı hatası."}, 500

    except RequestException as e:
        runpod_logger.error(f"RunPod isteğinde bir hata oluştu: {str(e)} -- user_id: {user_id} - username: {username}")
        return {"message": f"RunPod isteğinde bir hata oluştu: {str(e)}"}, 500

    except KeyError as ke:
        runpod_logger.error(f"RunPod yanıtında anahtar hatası: {str(ke)} -- user_id: {user_id} - username: {username}")
        return {"message": str(ke)}, 500




