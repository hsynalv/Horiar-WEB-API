from flask import current_app
from bson import ObjectId
from app.models.package_model import Package
from bson.errors import InvalidId

class PackageService:
    @staticmethod
    def add_package(data):
        packages_collection = current_app.db["packages"]

        # Eksik alan kontrolü
        if not data.get("name") or not data.get("credits") or not data.get("price"):
            raise ValueError("Missing required fields")

        # İndirimli fiyat kontrolü
        if data.get("discounted_price", data.get("price")) > data.get("price"):
            raise ValueError("Discounted price cannot be greater than the original price.")

        # Model kullanarak paket oluşturma
        package = Package.from_dict(data)

        result = packages_collection.insert_one(package.to_dict())
        return result.inserted_id

    @staticmethod
    def get_all_packages():
        packages_collection = current_app.db["packages"]
        packages = list(packages_collection.find())
        return [Package(**package).to_dict() for package in packages]

    @staticmethod
    def get_package_by_id(package_id):
        packages_collection = current_app.db["packages"]
        try:
            package = packages_collection.find_one({"_id": ObjectId(package_id)})
            if package:
                return Package(**package).to_dict()
            return None
        except InvalidId:
            return None

    @staticmethod
    def update_package(package_id, data):
        packages_collection = current_app.db["packages"]

        # Paket olup olmadığını kontrol et
        if not PackageService.get_package_by_id(package_id):
            raise ValueError("Package not found")

        # Eksik alan kontrolü
        if not data.get("name") or not data.get("credits") or not data.get("price"):
            raise ValueError("Missing required fields")

        # İndirimli fiyat kontrolü
        if data.get("discounted_price", data.get("price")) > data.get("price"):
            raise ValueError("Discounted price cannot be greater than the original price.")

        # Model kullanarak güncelleme işlemi
        updated_package = Package.from_dict(data)
        update_data = updated_package.to_dict()

        try:
            packages_collection.update_one({"_id": ObjectId(package_id)}, {"$set": update_data})
        except InvalidId:
            raise ValueError("Invalid package ID")

    @staticmethod
    def delete_package(package_id):
        packages_collection = current_app.db["packages"]
        try:
            result = packages_collection.delete_one({"_id": ObjectId(package_id)})
            return result.deleted_count > 0
        except InvalidId:
            raise ValueError("Invalid package ID")
