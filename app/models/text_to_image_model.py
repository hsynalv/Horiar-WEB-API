from flask_mongoengine import Document
from mongoengine.fields import StringField, IntField, FloatField, DateTimeField, DecimalField


class TextToImage(Document):
    discord_id = StringField(required=False)
    discord_username = StringField(required=False)
    guild = StringField()
    channel = StringField()
    datetime = DateTimeField(required=True)
    prompt = StringField(required=True)
    seed = IntField()
    model_type = StringField()
    prompt_fix = StringField()
    resolution = StringField()
    image_url = StringField()
    cost = DecimalField(precision=20, rounding='ROUND_HALF_UP', required=False)
    execution_time = IntField()
    source = StringField()
    user_id = StringField()
    username = StringField()

    meta = {'collection': 'text_to_image'}

    def to_dict(self):
        return {
            "_id": str(self.id),
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "guild": self.guild,
            "channel": self.channel,
            "datetime": self.datetime.strftime('%Y-%m-%d %H:%M:%S.%f') if self.datetime else None,
            "prompt": self.prompt,
            "seed": self.seed,
            "model_type": self.model_type,
            "prompt_fix": self.prompt_fix,
            "resolution": self.resolution,
            "image_url": self.image_url,
            "cost": self.cost,
            "execution_time": self.execution_time,
            "source": self.source,
            "user_id": self.user_id,
            "username": self.username
        }
