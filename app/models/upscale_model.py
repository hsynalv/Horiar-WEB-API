from flask_mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, FloatField

class Upscale(Document):
    discord_id = StringField(required=False)  # Discord ID
    discord_username = StringField(required=False)  # Discord Kullanıcı Adı
    datetime = DateTimeField(required=True)  # İşlem Tarihi
    low_res_image_url = StringField(required=True)  # Düşük çözünürlüklü görüntü URL
    high_res_image_url = StringField(required=True)  # Yüksek çözünürlüklü görüntü URL (opsiyonel)
    image_url_webp = StringField()
    cost = FloatField(required=True)  # İşlem maliyeti
    execution_time = FloatField(required=True)  # İşlem süresi (milisaniye)
    user_id = StringField(required=False)  # Kullanıcı ID
    username = StringField(required=False)
    source = StringField(required=False)  # İstek kaynağı (Discord vb.)

    meta = {
        'collection': 'upscale_requests'  # Veritabanında kullanılacak koleksiyon adı
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "datetime": self.datetime,
            "low_res_image_url": self.low_res_image_url,
            "high_res_image_url": self.high_res_image_url,
            "image_url_webp": self.image_url_webp,
            "cost": self.cost,
            "execution_time": self.execution_time,
            "user_id": self.user_id,
            "username": self.username,
            "source": self.source
        }

    def to_dict_frontend(self):
        return {
            "datetime": self.datetime,
            "low_res_image_url": self.low_res_image_url,
            "high_res_image_url": self.high_res_image_url,
            "image_url_webp": self.image_url_webp,
        }