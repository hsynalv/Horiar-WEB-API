from flask import current_app
from bson import ObjectId
from bson.errors import InvalidId

class PackageService:
    @staticmethod
    def add_package(package_data):
        if package_data["discounted_price"] > package_data["price"]:
            raise ValueError("Discounted price cannot be greater than the original price.")

        packages_collection = current_app.db["packages"]
        result = packages_collection.insert_one(package_data)
        return result.inserted_id

    @staticmethod
    def get_all_packages():
        packages_collection = current_app.db["packages"]
        packages = list(packages_collection.find())
        return [{"_id": str(package["_id"]), "name": package["name"], "credits": package["credits"], "price": package["price"], "discounted_price": package.get("discounted_price")} for package in packages]

    @staticmethod
    def update_package(package_id, update_data):
        packages_collection = current_app.db["packages"]

        try:
            result = packages_collection.update_one({"_id": ObjectId(package_id)}, {"$set": update_data})
            if result.matched_count == 0:
                return None  # Güncellenen paket bulunamadı
            return result.matched_count
        except InvalidId:
            return None  # Geçersiz ObjectId durumunda None döndür

    @staticmethod
    def delete_package(package_id):
        packages_collection = current_app.db["packages"]

        try:
            result = packages_collection.delete_one({"_id": ObjectId(package_id)})
            if result.deleted_count == 0:
                return None  # Paket bulunamadı
            return result.deleted_count
        except InvalidId:
            return None  # Geçersiz ObjectId durumunda None döndür

    @staticmethod
    def get_package_by_id(package_id):
        packages_collection = current_app.db["packages"]
        try:
            package = packages_collection.find_one({"_id": ObjectId(package_id)})
            if package:
                return {
                    "_id": str(package["_id"]),
                    "name": package["name"],
                    "credits": package["credits"],
                    "price": package["price"],
                    "discounted_price": package.get("discounted_price")
                }
            return None
        except InvalidId:
            return None  # Geçersiz ObjectId olduğunda None döndür