from flask import current_app
from bson import ObjectId
from app.models.user_model import User
from werkzeug.security import generate_password_hash, check_password_hash
from bson.errors import InvalidId
import re

class UserService:
    @staticmethod
    def add_user(email, password, username):
        # Eksik alan kontrolü
        if not email or not password or not username:
            raise ValueError("Missing required fields")

        # Geçersiz e-posta formatı kontrolü
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        users_collection = User.objects(email=email).first()

        # Eğer kullanıcı mevcutsa hata fırlat
        if users_collection:
            raise ValueError("User with this email already exists")

        # Kullanıcıyı MongoEngine ile oluşturma
        hashed_password = generate_password_hash(password)
        user = User(email=email, username=username, password=hashed_password)
        user.save()  # MongoEngine'de save metodu ile kullanıcı kaydedilir
        return str(user.id)

    @staticmethod
    def find_user_by_email(email):
        return User.objects(email=email).first()

    @staticmethod
    def check_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)

    @staticmethod
    def add_or_update_user(user_data):
        # Google veya Discord ID'ye göre kullanıcıyı bul
        if user_data.get("google_id"):
            user = User.objects(google_id=user_data["google_id"]).first()
        elif user_data.get("discord_id"):
            user = User.objects(discord_id=user_data["discord_id"]).first()
        else:
            user = None

        if user:
            user.update(**user_data)
        else:
            user = User(**user_data)
            user.save()

        return str(user.id)

    @staticmethod
    def get_user_by_id(user_id):
        return User.objects(id=user_id).first()

    @staticmethod
    def update_user_by_id(user_id, update_data):
        User.objects(id=user_id).update(**update_data)
