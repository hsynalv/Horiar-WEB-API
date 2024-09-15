from flask_mongoengine import Document
from mongoengine.fields import StringField, DateTimeField

class DiscordImageRequest(Document):
    user_id = StringField(required=True)
    username = StringField(required=True)
    prompt = StringField(required=True)
    datetime = DateTimeField(required=True)
    guild = StringField()

    meta = {
        'collection': 'image_requests_from_discord'  # MongoDB'deki koleksiyon adı
    }
