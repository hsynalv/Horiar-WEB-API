from mongoengine import Document, StringField, DateTimeField, FloatField
from datetime import datetime

class ImageToImage(Document):
    discord_id = StringField()
    discord_username = StringField()
    datetime = DateTimeField(default=datetime.utcnow ,required=True)
    ref_image = StringField(required=True)
    image = StringField(required=True)
    cost = FloatField()
    execution_time = FloatField()
    user_id = StringField(required=True)
    username = StringField()
    source = StringField()
    image_url_webp = StringField()
    prompt = StringField(required=True)

    meta = {
        'collection': 'image_to_image',
        'indexes': [
            'user_id',
            'datetime',
            'discord_id'
        ]
    }

    def to_dict(self):
        return {
            "id": self.id,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "datetime": self.datetime.isoformat() if self.datetime else None,
            "ref_image": self.ref_image,
            "image": self.image,
            "cost": self.cost,
            "execution_time": self.execution_time,
            "user_id": self.user_id,
            "username": self.username,
            "source": self.source,
            "image_url_webp": self.image_url_webp,
            "prompt": self.prompt
        }
