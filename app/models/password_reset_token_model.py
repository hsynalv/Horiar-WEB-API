from mongoengine import Document, StringField, ReferenceField, DateTimeField
from datetime import datetime, timedelta

class PasswordResetToken(Document):
    user = ReferenceField('User', required=True)  # Kullanıcıya referans
    token = StringField(required=True, unique=True)  # Benzersiz token
    expiration_date = DateTimeField(required=True)  # Token'ın geçerlilik tarihi
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'password_reset_tokens'
    }

    @classmethod
    def create_token_for_user(cls, user, token, expires_in=3600):
        """
        Kullanıcı için belirli bir süre (saniye cinsinden, varsayılan 1 saat) geçerli bir token oluşturur.
        """
        expiration_date = datetime.utcnow() + timedelta(seconds=expires_in)
        return cls(user=user, token=token, expiration_date=expiration_date).save()