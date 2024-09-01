from flask import current_app


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
        else:
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
    @staticmethod
    def update_user_by_google_id(user_id, update_data):
        users_collection = current_app.db["users"]
        users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )