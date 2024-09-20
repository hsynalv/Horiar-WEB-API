# /app/models/user_model.py
from mongoengine.fields import StringField, BooleanField, EmailField, ListField
from flask_mongoengine import Document
from flask_login import UserMixin

class User(UserMixin,Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, max_length=50)
    password = StringField()
    google_id = StringField()
    google_username = StringField()
    discord_id = StringField()
    discord_username = StringField()

    # Rol alanı ekliyoruz (örn. 'admin', 'user')
    roles = ListField(StringField(), default=["37fb8744-faf9-4f62-a729-a284c842bf0a"])  # Varsayılan rol 'user'

    # Veritabanı alanı olarak 'is_enabled' kullanılıyor
    is_enabled = BooleanField(default=True)
    is_banned = BooleanField(default=False)

    meta = {'collection': 'users'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "google_id": self.google_id,
            "google_username": self.google_username,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "roles": self.roles,
            "is_enabled": self.is_enabled,
            "is_banned": self.is_banned
        }

    # Flask-Login için metodlar
    def get_id(self):
        return str(self.id)
    def is_authenticated(self):
        return True
    def is_active(self):  # Flask-Login için `is_active` metodu
        return self.is_enabled
    def is_anonymous(self):
        return False
