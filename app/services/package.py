from flask import current_app
from bson import ObjectId
from app.models.package_model import Package
from bson.errors import InvalidId

class PackageService:
    @staticmethod
    def add_package(data):
        # Eksik alan kontrolü
        if not data.get("name") or not data.get("credits") or not data.get("price"):
            raise ValueError("Missing required fields")

        # İndirimli fiyat kontrolü
        if data.get("discounted_price", data.get("price")) > data.get("price"):
            raise ValueError("Discounted price cannot be greater than the original price.")

        # Model kullanarak paket oluşturma
        package = Package(**data)
        package.save()

        return str(package.id)

    @staticmethod
    def get_all_packages():
        packages = Package.objects()
        return [package.to_dict() for package in packages]

    @staticmethod
    def get_package_by_id(package_id):
        package = Package.objects(id=package_id).first()
        if package:
            return package.to_dict()
        return None

    @staticmethod
    def update_package(package_id, data):
        # Paket olup olmadığını kontrol et
        package = Package.objects(id=package_id).first()
        if not package:
            raise ValueError("Package not found")

        # İndirimli fiyat kontrolü
        if data.get("discounted_price", data.get("price")) > data.get("price"):
            raise ValueError("Discounted price cannot be greater than the original price.")

        package.update(**data)

    @staticmethod
    def delete_package(package_id):
        package = Package.objects(id=package_id).first()
        if package:
            package.delete()
            return True
        return False
