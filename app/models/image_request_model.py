from mongoengine import Document, StringField, DateTimeField
from datetime import datetime
import pytz

class ImageRequest(Document):
    user_id = StringField(required=True)
    username = StringField(required=True, max_length=50)
    prompt = StringField(required=True)
    image = StringField(required=True)
    request_time = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'image_requests'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "image": self.image,
            "request_time": self.request_time
        }
