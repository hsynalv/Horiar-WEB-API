from flask import current_app


class UserService:
    @staticmethod
    def add_or_update_user(user_data):
        """
        Kullanıcıyı MongoDB'ye ekler veya günceller.
        """
        users_collection = current_app.db["users"]

        # Discord ID'sine göre kullanıcıyı bul veya oluştur
        existing_user = users_collection.find_one({"discord_id": user_data["discord_id"]})

        if existing_user:
            # Kullanıcıyı güncelle
            users_collection.update_one(
                {"discord_id": user_data["discord_id"]},
                {"$set": user_data}
            )
        else:
            # Yeni kullanıcıyı ekle
            users_collection.insert_one(user_data)

    @staticmethod
    def get_user_by_discord_id(discord_id):
        """
        Discord ID'ye göre kullanıcıyı bulur.
        """
        users_collection = current_app.db["users"]
        return users_collection.find_one({"discord_id": discord_id})

    @staticmethod
    def get_all_users():
        """
        Tüm kullanıcıları getirir.
        """
        users_collection = current_app.db["users"]
        return list(users_collection.find({}))
