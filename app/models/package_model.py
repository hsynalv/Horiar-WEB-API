from mongoengine.fields import StringField, FloatField, ReferenceField, ListField
from flask_mongoengine import Document

class Package(Document):
    title = StringField(required=True, max_length=100)
    monthly_original_price = FloatField(required=True)
    yearly_original_price = FloatField(required=True)
    monthly_sale_price = FloatField()
    yearly_sale_price = FloatField()
    features = ListField(ReferenceField('Feature'))  # Özelliklere referans

    meta = {'collection': 'packages'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "monthly_original_price": self.monthly_original_price,
            "yearly_original_price": self.yearly_original_price,
            "monthly_sale_price": self.monthly_sale_price,
            "yearly_sale_price": self.yearly_sale_price,
            "features": [str(feature.id) for feature in self.features] if self.features else []
        }
