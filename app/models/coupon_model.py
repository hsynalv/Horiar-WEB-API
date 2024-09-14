# /app/models/coupon_model.py
from mongoengine import Document, StringField, FloatField, BooleanField, DateTimeField, IntField, ListField, ReferenceField
from datetime import datetime
from app.models.user_model import User

class Coupon(Document):
    name = StringField(required=True, max_length=100, unique=True)
    discount_percentage = FloatField(required=True)
    valid_until = DateTimeField(required=True)
    is_active = BooleanField(default=True)
    max_usage = IntField(required=True)  # Maksimum kullanım sayısı zorunlu bir alan
    usage_count = IntField(default=0)  # Varsayılan olarak 0 kullanım sayısı

    used_by = ListField(ReferenceField(User))  # Kuponu kullanan kullanıcılar

    meta = {'collection': 'coupons'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "discount_percentage": self.discount_percentage,
            "valid_until": self.valid_until,
            "is_active": self.is_active,
            "max_usage": self.max_usage,
            "usage_count": self.usage_count,
            "used_by": [str(user.id) for user in self.used_by]  # Kullanıcıların ID'lerini döndürüyoruz
        }
