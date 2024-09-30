# /app/models/feature_model.py
from flask_mongoengine import Document
from mongoengine.fields import StringField


class Feature(Document):
    name = StringField(required=True, unique=True, max_length=200)

    meta = {'collection': 'features'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name
        }
