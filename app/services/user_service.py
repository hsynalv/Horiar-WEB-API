from flask import current_app
from bson import ObjectId
from app.errors.not_found_error import NotFoundError
from app.models.user_model import User
from passlib.hash import pbkdf2_sha256  # passlib ile pbkdf2_sha256 kullanımı
import re
import datetime

from app.services.base_service import BaseService
from app.services.subscription_service import SubscriptionService


class UserService(BaseService):
    model = User

    @staticmethod
    def add_or_update_user(user_data):
        """
        Kullanıcıyı ekler veya günceller.
        """
        user = UserService.model.objects(email=user_data["email"]).first()

        if user:
            if user_data.get("google_id"):
                user.google_id = user_data["google_id"]
                user.google_username = user_data["google_username"]
            elif user_data.get("discord_id"):
                user.discord_id = user_data["discord_id"]
                user.discord_username = user_data["discord_username"]

            # Son giriş tarihini güncelle
            user.last_login_date = datetime.datetime.utcnow()
            user.save()  # Değişiklikleri kaydetmek için save() kullanılır
        else:
            user_data["registration_date"] = datetime.datetime.utcnow()
            user = User(**user_data)
            user.save()

        return user  # Artık user id yerine tüm user nesnesini döndürüyoruz

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
        if stored_password is None:
            raise ValueError("Kullanıcının şifresi yok")  # Şifre yoksa hata fırlat
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

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Kullanıcının şifresini değiştirir.
        """
        # Kullanıcıyı al
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        # Mevcut şifreyi doğrula
        if not pbkdf2_sha256.verify(current_password, user.password):
            raise ValueError("Current password is incorrect")

        # Yeni şifreyi hash'le ve güncelle
        user.password = pbkdf2_sha256.hash(new_password)
        user.save()

    @staticmethod
    def get_all_users():
        """
        Tüm kullanıcıları döndürür.
        """
        return User.objects().all()

    @staticmethod
    def get_user_credit(user_id):
        subscription = SubscriptionService.get_subscription_by_id(user_id)

        if subscription:
            return {
                    "currentCredit": int(subscription.credit_balance),
                    "maxCredit":int(subscription.max_credit_balance)
            }

        user = UserService.get_user_by_id(user_id)
        return {
                    "currentCredit": int(subscription.base_credits),
                    "maxCredit": 15
        }