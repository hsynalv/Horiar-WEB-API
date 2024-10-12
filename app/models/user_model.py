from mongoengine.fields import StringField, BooleanField, EmailField, ListField, DateTimeField, IntField
from flask_mongoengine import Document
from flask_login import UserMixin
import datetime



class User(UserMixin, Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, max_length=50)
    password = StringField()
    google_id = StringField()
    google_username = StringField()
    discord_id = StringField()
    discord_username = StringField()
    base_credits = IntField(default=15)

    # Rol alanı ekliyoruz (örn. 'admin', 'user')
    roles = ListField(StringField(), default=["37fb8744-faf9-4f62-a729-a284c842bf0a"])  # Varsayılan rol 'user'

    # Kullanıcının durumu
    is_enabled = BooleanField(default=True)
    is_banned = BooleanField(default=False)

    # Yeni eklenen alanlar
    registration_date = DateTimeField(default=datetime.datetime.utcnow)  # Kullanıcı kayıt tarihi
    last_login_date = DateTimeField()  # Son giriş tarihi

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
            "is_banned": self.is_banned,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "last_login_date": self.last_login_date.isoformat() if self.last_login_date else None,
            "base_credits": self.base_credits,
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
