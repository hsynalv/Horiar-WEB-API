from bson import ObjectId
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash


class UserService:
    @staticmethod
    def add_or_update_user(user_data):
        users_collection = current_app.db["users"]

        if "google_id" in user_data:
            existing_user = users_collection.find_one({"google_id": user_data["google_id"]})
        elif "discord_id" in user_data:
            existing_user = users_collection.find_one({"discord_id": user_data["discord_id"]})
        else:
            existing_user = None

        if existing_user:
            users_collection.update_one(
                {"_id": existing_user["_id"]},
                {"$set": user_data}
            )
            return existing_user["_id"]
        else:
            inserted_user = users_collection.insert_one(user_data)
            return inserted_user.inserted_id

    @staticmethod
    def get_user_by_discord_id(discord_id):
        """
        Discord ID'ye göre kullanıcıyı bulur.
        """
        users_collection = current_app.db["users"]
        return users_collection.find_one({"discord_id": discord_id})

    @staticmethod
    def get_user_by_id(id):
        """
        Discord ID'ye göre kullanıcıyı bulur.
        """
        users_collection = current_app.db["users"]
        return users_collection.find_one({"_id": ObjectId(id)})

    @staticmethod
    def get_all_users():
        """
        Tüm kullanıcıları getirir.
        """
        users_collection = current_app.db["users"]
        return list(users_collection.find({}))
    @staticmethod
    def update_user_by_google_id(user_id, update_data):
        users_collection = current_app.db["users"]
        users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )

    @staticmethod
    def add_user(email, password, username):
        users_collection = current_app.db["users"]

        # Kullanıcının zaten var olup olmadığını kontrol et
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return None

        # Şifreyi hashle ve kullanıcıyı ekle
        hashed_password = generate_password_hash(password)
        user_id = users_collection.insert_one({
            "email": email,
            "password": hashed_password,
            "username": username,
            "discord_id": None,
            "discord_username": None,
            "google_id": None,

        }).inserted_id


        return str(user_id)

    @staticmethod
    def find_user_by_email(email):
        users_collection = current_app.db["users"]
        return users_collection.find_one({"email": email})

    @staticmethod
    def check_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)