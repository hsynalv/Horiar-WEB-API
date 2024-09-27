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
    re_request = BooleanField(default=False)  # Yeniden istek yapıldı mı?
    execution_time = FloatField()  #
    spent_money = DecimalField(precision=20, rounding='ROUND_HALF_UP', required=False, db_field='spent_money($)')  # Harcanan para ($)


    meta = {
        'collection': 'image_requests_from_discord'  # MongoDB'deki koleksiyon adı
    }
