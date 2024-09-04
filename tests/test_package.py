import unittest
from mongomock import MongoClient
from flask import Flask
from app.services.package import PackageService
from app import create_app
from bson import ObjectId

class TestPackageService(unittest.TestCase):

    def setUp(self):
        # Flask uygulamasını oluştur ve test için bağlamını başlat
        self.app = create_app()
        self.app.config['TESTING'] = True

        self.app_context = self.app.app_context()
        self.app_context.push()

        # Mock MongoClient
        self.client = MongoClient()
        self.db = self.client['horiar']
        self.packages_collection = self.db['packages']

        self.app.db = self.db

    def tearDown(self):
        self.app_context.pop()

    def test_add_package_success(self):
        data = {
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }

        package_id = PackageService.add_package(data)
        self.assertIsNotNone(package_id)
        self.assertIsInstance(package_id, ObjectId)

    def test_add_package_missing_fields(self):
        data = {
            "credits": 100,
            "price": 10
        }

        with self.assertRaises(ValueError):
            PackageService.add_package(data)

    def test_add_package_invalid_discount(self):
        data = {
            "name": "Premium Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 20
        }

        with self.assertRaises(ValueError):
            PackageService.add_package(data)

    def test_update_package_success(self):
        package_id = self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }).inserted_id

        update_data = {
            "name": "Updated Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 12
        }

        PackageService.update_package(str(package_id), update_data)
        updated_package = self.packages_collection.find_one({"_id": package_id})
        self.assertEqual(updated_package["name"], "Updated Package")

    def test_delete_package_success(self):
        package_id = self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }).inserted_id

        result = PackageService.delete_package(str(package_id))
        self.assertTrue(result)

    def test_delete_package_invalid_id(self):
        with self.assertRaises(ValueError):
            PackageService.delete_package("invalid_id")
