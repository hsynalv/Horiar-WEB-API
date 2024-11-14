from flask_mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, FloatField
from datetime import datetime

class ImageToVideo(Document):
    user_id = StringField(required=True)  # Kullanıcı ID'si
    username = StringField(required=True)  # Kullanıcı adı
    prompt = StringField(required=True)  # İstek prompt'u
    image_url = StringField(required=True)  # Görüntü URL'si
    cost = FloatField(required=True)  # İşlem maliyeti
    execution_time = FloatField(required=True)  # İşlem süresi
    video_url = StringField(required=True)  # Video URL'si
    datetime = DateTimeField(default=datetime.utcnow, required=True)  # Date and time of the request

    meta = {
        'collection': 'image_to_video'  # Veritabanındaki koleksiyon adı
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "image_url": self.image_url,
            "cost": self.cost,
            "execution_time": self.execution_time,
            "video_url": self.video_url,
            "datetime": self.datetime
        }

    def to_dict_frontend(self):
        return {
            "prompt": self.prompt,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "datetime": self.datetime
        }
