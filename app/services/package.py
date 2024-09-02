from flask import current_app
from bson import ObjectId

class PackageService:
    @staticmethod
    def add_package(package_data):
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
        packages_collection.update_one({"_id": ObjectId(package_id)}, {"$set": update_data})

    @staticmethod
    def delete_package(package_id):
        packages_collection = current_app.db["packages"]
        packages_collection.delete_one({"_id": ObjectId(package_id)})

    @staticmethod
    def get_package_by_id(package_id):
        packages_collection = current_app.db["packages"]
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