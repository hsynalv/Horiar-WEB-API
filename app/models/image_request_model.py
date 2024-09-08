from datetime import datetime
from bson import ObjectId
import pytz

class ImageRequest:
    def __init__(self, user_id, username, prompt, image, request_time=None, _id=None):
        self._id = _id  # Veritabanı için ID
        self.user_id = user_id
        self.username = username
        self.prompt = prompt
        self.image = image  # Yeni eklenen image alanı

        # Türkiye saat dilimine göre zaman ayarlama (UTC+3)
        tz = pytz.timezone('Europe/Istanbul')
        local_time = datetime.now(tz)

        # Zamanı UTC'ye çeviriyoruz
        self.request_time = request_time or local_time.astimezone(pytz.utc)

    def to_dict(self):
        image_request_dict = {
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "image": self.image,  # image alanını da sözlüğe ekle
            "request_time": self.request_time  # Zaman UTC olarak kaydedilecek
        }

        if self._id:
            image_request_dict["_id"] = str(self._id)

        return image_request_dict

    @staticmethod
    def from_dict(data):
        # Eğer UTC kaydedilmiş bir zamanı yerel saate çevirmek istersen
        utc_time = data.get("request_time")
        tz = pytz.timezone('Europe/Istanbul')
        local_time = utc_time.astimezone(tz)

        return ImageRequest(
            user_id=data.get("user_id"),
            username=data.get("username"),
            prompt=data.get("prompt"),
            image=data.get("image"),  # Veriyi alırken image alanını da ekle
            request_time=local_time,  # Zamanı yerel saate çevirdik
            _id=data.get("_id")
        )
