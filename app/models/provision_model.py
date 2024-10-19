from flask_mongoengine import Document
from mongoengine import StringField, BooleanField

from app.models.package_model import Package
from app.models.user_model import User


class Provision(Document):
    merchant_oid = StringField(required=True, unique=True)
    username = StringField(required=True, max_length=100)
    user_id = StringField(required=True)
    package_id = StringField(required=True)
    is_annual = BooleanField(default=False)
    email = StringField(required=True)
    used_coupon = StringField(required=False)

    meta = {'collection': 'provision'}

    def to_dict(self):
        return {
            "merchant_oid": self.merchant_oid,
            "username": self.username,
            "user_id": str(self.user_id.id),
            "package_id": str(self.package_id.id),
            "is_annual": self.is_annual,
            "email": self.email,
            "used_coupon": self.used_coupon,
        }