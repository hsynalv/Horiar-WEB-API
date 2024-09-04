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

        # Uygulama bağlamı
        self.app_context = self.app.app_context()
        self.app_context.push()

        # MongoClient'ı mock olarak oluştur
        self.client = MongoClient()
        self.db = self.client['horiar']
        self.packages_collection = self.db['packages']

        # Uygulama bağlamına mock veritabanını ekle
        self.app.db = self.db

    def tearDown(self):
        # Testler bittikten sonra uygulama bağlamını temizle
        self.app_context.pop()

    def test_add_package(self):
        # Paket verisi oluşturalım
        package_data = {
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }

        # Paket ekleme fonksiyonunu test edelim
        package_id = PackageService.add_package(package_data)
        self.assertIsNotNone(package_id)
        self.assertIsInstance(package_id, ObjectId)

        # Eklenen paketi veritabanında kontrol edelim
        package = self.packages_collection.find_one({"_id": package_id})
        self.assertIsNotNone(package)
        self.assertEqual(package["name"], "Basic Package")

    def test_get_all_packages(self):
        # Paket ekleyelim
        self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })

        # Paketleri getirme fonksiyonunu test edelim
        packages = PackageService.get_all_packages()
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["name"], "Basic Package")

    def test_update_package(self):
        # Paket ekleyelim
        package_id = self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }).inserted_id

        # Paket güncelleme fonksiyonunu test edelim
        update_data = {
            "name": "Updated Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 12
        }
        PackageService.update_package(str(package_id), update_data)

        # Güncellenen paketi kontrol edelim
        updated_package = self.packages_collection.find_one({"_id": package_id})
        self.assertEqual(updated_package["name"], "Updated Package")
        self.assertEqual(updated_package["credits"], 200)

    def test_delete_package(self):
        # Paket ekleyelim
        package_id = self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }).inserted_id

        # Paket silme fonksiyonunu test edelim
        PackageService.delete_package(str(package_id))

        # Silinen paketin var olup olmadığını kontrol edelim
        deleted_package = self.packages_collection.find_one({"_id": package_id})
        self.assertIsNone(deleted_package)

    def test_get_package_by_id(self):
        # Paket ekleyelim
        package_id = self.packages_collection.insert_one({
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        }).inserted_id

        # Paket bulma fonksiyonunu test edelim
        package = PackageService.get_package_by_id(str(package_id))
        self.assertIsNotNone(package)
        self.assertEqual(package["name"], "Basic Package")

    def test_add_package_with_missing_data(self):
        # Eksik veri ile paket eklemeye çalışalım
        package_data = {
            "credits": 100,
            "price": 10
        }

        with self.assertRaises(KeyError):
            PackageService.add_package(package_data)  # İsim eksik olduğunda hata beklenir

    def test_update_package_with_invalid_id(self):
        # Geçersiz bir package_id ile güncelleme yapmaya çalışalım
        update_data = {
            "name": "Updated Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 12
        }
        result = PackageService.update_package("invalid_id", update_data)
        self.assertIsNone(result)  # Geçersiz ID durumunda None dönmeli

    def test_delete_package_with_invalid_id(self):
        # Geçersiz bir package_id ile silme işlemi yapmaya çalışalım
        result = PackageService.delete_package("invalid_id")
        self.assertIsNone(result)  # Geçersiz ID durumunda None dönmeli

    def test_add_package_with_invalid_discount(self):
        # İndirimli fiyatın, normal fiyattan büyük olduğu senaryo
        package_data = {
            "name": "Premium Package",
            "credits": 200,
            "price": 10,
            "discounted_price": 15  # İndirimli fiyat, normal fiyattan büyük
        }

        # Geçersiz indirimli fiyatın nasıl ele alındığını test edelim
        with self.assertRaises(ValueError):
            PackageService.add_package(package_data)


if __name__ == '__main__':
    unittest.main()
