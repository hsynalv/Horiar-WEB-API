from flask_mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, IntField, BooleanField, FloatField, DecimalField

class DiscordImageRequest(Document):
    user_id = StringField(required=True)
    username = StringField(required=True)
    prompt = StringField(required=True)
    datetime = DateTimeField(required=True)
    guild = StringField()
    channel = StringField(required=False)

    resolution = StringField(required=False)  # Örnek: "1920x1080"
    aspect_ratio = StringField(required=False)  # Örnek: "16:9"
    seed = IntField(required=False)  # Örnek: 2752667741 gibi bir sayı
    prompt_fix = StringField()  # Prompt düzeltmeleri
    model_type = StringField()  # Kullanılan model türü (Örnek: "clip_l" veya "t5xxl")
    re_request = BooleanField(default=False, db_field="re-request")  # Yeniden istek yapıldı mı?
    execution_time = FloatField()  #
    spent_money = DecimalField(precision=20, rounding='ROUND_HALF_UP', required=False, db_field='spent_money($)')  # Harcanan para ($)
    # Yeni eklenen alanlar
    cost = DecimalField(precision=20, rounding='ROUND_HALF_UP', required=False)  # Bu işlem için toplam maliyet
    time = FloatField(required=False)  # Bu işlem için geçen zaman

    meta = {
        'collection': 'image_requests_from_discord'  # MongoDB'deki koleksiyon adı
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "datetime": self.datetime.strftime('%Y-%m-%d %H:%M:%S') if self.datetime else None,
            "guild": self.guild,
            "channel": self.channel,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "seed": self.seed,
            "prompt_fix": self.prompt_fix,
            "model_type": self.model_type,
            "re_request": self.re_request,
            "execution_time": self.execution_time,
            "spent_money": float(self.spent_money) if self.spent_money else None,
            "cost": float(self.cost) if self.cost else None,
            "time": self.time
        }
