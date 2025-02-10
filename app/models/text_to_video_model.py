from flask_mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, FloatField
from datetime import datetime

class TextToVideoGeneration(Document):
    user_id = StringField(required=True)  # User ID
    username = StringField(required=True)  # Username
    prompt = StringField(required=True)  # Text prompt used for video generation
    cost = FloatField(required=False)  # Cost of the video generation process
    execution_time = FloatField(required=False)  # Execution time in milliseconds
    video_url = StringField(required=True)  # URL of the generated video
    datetime = DateTimeField(default=datetime.utcnow, required=True)  # Date and time of the request

    meta = {
        'db_alias': "default",
        'collection': 'text_to_video'  # Collection name in the database
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "cost": self.cost,
            "execution_time": self.execution_time,
            "video_url": self.video_url,
            "datetime": self.datetime
        }

    def to_dict_frontend(self):
        return {
            "prompt": self.prompt,
            "video_url": self.video_url,
            "datetime": self.datetime
        }
