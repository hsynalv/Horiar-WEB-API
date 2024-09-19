# /app/models/user_model.py
from mongoengine.fields import StringField, BooleanField, EmailField, ListField
from flask_mongoengine import Document

class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, max_length=50)
    password = StringField()
    google_id = StringField()
    google_username = StringField()
    discord_id = StringField()
    discord_username = StringField()

    # Rol alanı ekliyoruz (örn. 'admin', 'user')
    roles = ListField(StringField(), default=["37fb8744-faf9-4f62-a729-a284c842bf0a"])  # Varsayılan rol 'user'

    is_active = BooleanField(default=True)  # Kullanıcı aktif mi?
    is_banned = BooleanField(default=False)  # Kullanıcı yasaklı mı?

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
            "is_active": self.is_active,
            "is_banned": self.is_banned
        }
