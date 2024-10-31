import json
import logging
import requests
from requests import Timeout, RequestException

# Özel logger'ı alıyoruz
runpod_logger = logging.getLogger("runpod")

def send_runpod_request(app, data, user_id, username, runpod_url, timeout=360):
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

        if response.status_code != 200:
            response.raise_for_status()
            logging.error(response.text)  # Genel hata logu

        result = response.json()
        outer_status = result.get("status")
        inner_status = result.get("output", {}).get("status")
        message = result.get("output", {}).get("message")

        if outer_status != "COMPLETED" or inner_status != "success":
            runpod_logger.warning("---------------------------------------------------------------------------------")
            runpod_logger.error(result)
            runpod_logger.error(f"RunPod kaynaklı hata meydana geldi. (An error occurred: RunPod request did not complete successfully.) user_id: {user_id} - username: {username}")
            runpod_logger.warning("---------------------------------------------------------------------------------")

            return {"message": "An error occurred: RunPod request did not complete successfully."}, 500

        if message is None:
            runpod_logger.warning("---------------------------------------------------------------------------------")
            runpod_logger.error(f"RunPod kaynaklı hata meydana geldi. (An error occurred while generating the image, please try again.) user_id: {user_id} - username: {username}")
            runpod_logger.warning("---------------------------------------------------------------------------------")
            raise KeyError("An error occurred while generating the image, please try again.")

        return result, 200

    except Timeout:
        runpod_logger.warning("---------------------------------------------------------------------------------")
        runpod_logger.error(f"RunPod isteği zaman aşımına uğradı! (RunPod isteği zaman aşımına uğradı.) user_id: {user_id} - username: {username}")
        runpod_logger.warning("---------------------------------------------------------------------------------")
        return {"message": "RunPod isteği zaman aşımına uğradı."}, 500

    except ConnectionError:
        runpod_logger.warning("---------------------------------------------------------------------------------")
        runpod_logger.error(f"RunPod bağlantı hatası! user_id: {user_id} - username: {username}")
        runpod_logger.warning("---------------------------------------------------------------------------------")
        return {"message": "RunPod bağlantı hatası."}, 500

    except RequestException as e:
        runpod_logger.error(f"RunPod isteğinde bir hata oluştu: {str(e)} -- user_id: {user_id} - username: {username}")
        return {"message": f"RunPod isteğinde bir hata oluştu: {str(e)}"}, 500

    except KeyError as ke:
        runpod_logger.error(f"RunPod yanıtında anahtar hatası: {str(ke)} -- user_id: {user_id} - username: {username}")
        return {"message": str(ke)}, 500




