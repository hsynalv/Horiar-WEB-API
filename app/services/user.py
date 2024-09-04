from flask import current_app
from bson import ObjectId
from app.models.user_model import User
from werkzeug.security import generate_password_hash, check_password_hash
from bson.errors import InvalidId
import re

class UserService:
    @staticmethod
    def add_user(email, password, username):
        users_collection = current_app.db["users"]

        # Eksik alan kontrolü
        if not email or not password or not username:
            raise ValueError("Missing required fields")

        # Geçersiz e-posta formatı kontrolü
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")

        # Kullanıcının zaten var olup olmadığını kontrol et
        if users_collection.find_one({"email": email}):
            raise ValueError("User already exists")

        # Şifreyi hash'le ve kullanıcıyı ekle
        hashed_password = generate_password_hash(password)
        user = User(email=email, username=username, password=hashed_password)
        result = users_collection.insert_one(user.to_dict())

        return str(result.inserted_id)

    @staticmethod
    def find_user_by_email(email):
        users_collection = current_app.db["users"]
        user_data = users_collection.find_one({"email": email})
        if user_data:
            return User.from_dict(user_data)
        return None

    @staticmethod
    def check_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)

    @staticmethod
    def add_or_update_user(user_data):
        users_collection = current_app.db["users"]

        # Google veya Discord ID'ye göre kullanıcıyı bul
        if user_data.get("google_id"):
            existing_user = users_collection.find_one({"google_id": user_data["google_id"]})
        elif user_data.get("discord_id"):
            existing_user = users_collection.find_one({"discord_id": user_data["discord_id"]})
        else:
            existing_user = None

        if existing_user:
            users_collection.update_one({"_id": existing_user["_id"]}, {"$set": user_data})
            return existing_user["_id"]
        else:
            user = User.from_dict(user_data)
            result = users_collection.insert_one(user.to_dict())
            return result.inserted_id

    @staticmethod
    def get_user_by_id(user_id):
        users_collection = current_app.db["users"]
        try:
            user_data = users_collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User.from_dict(user_data).to_dict()
            return None
        except InvalidId:
            return None

    @staticmethod
    def update_user_by_id(user_id, update_data):
        users_collection = current_app.db["users"]

        try:
            # ObjectId'nin geçerli olup olmadığını kontrol et
            if not ObjectId.is_valid(user_id):
                raise ValueError("Invalid user ID format")

            result = users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

            # Kullanıcı bulunmazsa
            if result.matched_count == 0:
                raise ValueError("User not found")

        except InvalidId:
            raise ValueError("Invalid user ID")
