from flask import current_app
from bson import ObjectId
from app.errors.not_found_error import NotFoundError
from app.models.user_model import User
from passlib.hash import pbkdf2_sha256  # passlib ile pbkdf2_sha256 kullanımı
import re

from app.services.base_service import BaseService


class UserService(BaseService):
    model = User

    @staticmethod
    def add_or_update_user(user_data):
        """
        Kullanıcıyı ekler veya günceller.
        """
        if user_data.get("google_id"):
            user = User.objects(google_id=user_data["google_id"]).first()
        elif user_data.get("discord_id"):
            user = User.objects(discord_id=user_data["discord_id"]).first()
        else:
            user = None

        if user:
            return str(user.id)
        else:
            user = User(**user_data)
            user.save()

        return str(user.id)

    @staticmethod
    def find_user_by_email(email):
        """
        E-posta ile kullanıcıyı bulur.
        """
        return User.objects(email=email).first()

    @staticmethod
    def check_password(stored_password, provided_password):
        """
        Kullanıcının şifresini doğrular. pbkdf2_sha256 kullanılıyor.
        """
        return pbkdf2_sha256.verify(provided_password, stored_password)

    @staticmethod
    def add_user(email, password, username):
        """
        Yeni bir kullanıcı ekler.
        """
        # Kullanıcı verilerini doğrula
        UserService.validate_user_data(email, password, username)

        # E-posta var mı kontrol et
        existing_user_email = User.objects(email=email).first()
        if existing_user_email:
            raise ValueError("User with this email already exists")

        # Kullanıcı adı var mı kontrol et
        existing_user_username = User.objects(username=username).first()
        if existing_user_username:
            raise ValueError("User with this username already exists")

        # Şifreyi hash'le ve kullanıcıyı ekle (pbkdf2_sha256 kullanılıyor)
        hashed_password = pbkdf2_sha256.hash(password)
        user = User(email=email, username=username, password=hashed_password)
        user.save()
        return str(user.id)

    @staticmethod
    def get_user_by_id(user_id):
        """
        Kullanıcıyı ID'ye göre getirir. Eğer kullanıcı bulunamazsa hata fırlatır.
        """
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        return user

    @staticmethod
    def update_user_by_id(user_id, update_data):
        """
        Kullanıcıyı ID ile günceller.
        """
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        user.update(**update_data)

    @staticmethod
    def validate_user_data(email, password, username):
        """
        Kullanıcı oluşturma verilerini doğrular.
        """
        if not email or not password or not username:
            raise ValueError("Missing required fields")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
