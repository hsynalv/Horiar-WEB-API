import unittest
from mongomock import MongoClient
from app.services.user_service import UserService
from app import create_app
from bson import ObjectId
from werkzeug.security import check_password_hash

class TestUserService(unittest.TestCase):

    def setUp(self):
        # Flask uygulamasını oluştur ve test için bağlamını başlat
        self.app = create_app()
        self.app.config['TESTING'] = True

        self.app_context = self.app.app_context()
        self.app_context.push()

        # Mock MongoClient
        self.client = MongoClient()
        self.db = self.client['horiar']
        self.users_collection = self.db['users']

        self.app.db = self.db

    def tearDown(self):
        self.app_context.pop()

    def test_add_user_success(self):
        user_id = UserService.add_user("test@example.com", "password123", "TestUser")
        self.assertIsNotNone(user_id)
        self.assertIsInstance(user_id, str)

        # Veritabanında kullanıcıyı kontrol edelim
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "test@example.com")
        self.assertTrue(check_password_hash(user["password"], "password123"))

    def test_add_user_already_exists(self):
        # İlk kullanıcıyı ekleyelim
        self.users_collection.insert_one({
            "email": "test@example.com",
            "password": "hashedpassword",
            "username": "TestUser"
        })

        # Aynı email ile ikinci kullanıcı eklemeye çalışalım
        with self.assertRaises(ValueError):
            UserService.add_user("test@example.com", "password123", "TestUser")

    def test_find_user_by_email(self):
        # Kullanıcıyı ekleyelim
        self.users_collection.insert_one({
            "email": "test@example.com",
            "password": "hashedpassword",
            "username": "TestUser"
        })

        # Kullanıcıyı email'e göre bulalım
        user = UserService.find_user_by_email("test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_check_password(self):
        # Şifre kontrol testi
        hashed_password = UserService.add_user("test@example.com", "password123", "TestUser")
        user = self.users_collection.find_one({"email": "test@example.com"})
        self.assertTrue(UserService.check_password(user["password"], "password123"))

    def test_add_or_update_user(self):
        # Yeni kullanıcı ekle
        user_data = {
            "email": "test2@example.com",
            "username": "TestUser2",
            "google_id": "google123",
            "discord_id": None
        }
        user_id = UserService.add_or_update_user(user_data)
        self.assertIsNotNone(user_id)

        # Aynı kullanıcıyı güncelle
        user_data["username"] = "UpdatedUser"
        updated_user_id = UserService.add_or_update_user(user_data)
        self.assertEqual(user_id, updated_user_id)

        # Kullanıcı verilerini kontrol et
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        self.assertEqual(user["username"], "UpdatedUser")

    def test_get_user_by_id(self):
        # Kullanıcıyı ekleyelim
        user_id = self.users_collection.insert_one({
            "email": "test@example.com",
            "password": "hashedpassword",
            "username": "TestUser"
        }).inserted_id

        # UserService üzerinden kullanıcıyı bul
        user = UserService.get_user_by_id(str(user_id))
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "test@example.com")

    def test_get_user_by_id_invalid(self):
        # Geçersiz ID ile kullanıcıyı bulmaya çalış
        user = UserService.get_user_by_id("invalid_id")
        self.assertIsNone(user)

    def test_update_user_by_id(self):
        # Kullanıcıyı ekleyelim
        user_id = self.users_collection.insert_one({
            "email": "test@example.com",
            "google_id": "google123",
            "username": "TestUser"
        }).inserted_id

        # Kullanıcıyı güncelle
        UserService.update_user_by_id(user_id, {"username": "UpdatedUser"})
        updated_user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        self.assertEqual(updated_user["username"], "UpdatedUser")

    def test_add_user_invalid_email(self):
        with self.assertRaises(ValueError):
            UserService.add_user("invalid_email", "password123", "TestUser")

    def test_password_is_hashed(self):
        user_id = UserService.add_user("test@example.com", "password123", "TestUser")
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        # Şifre hashlenmiş olmalı, yani düz metin olarak saklanmamalı
        self.assertNotEqual(user["password"], "password123")
        self.assertTrue(check_password_hash(user["password"], "password123"))

    def test_update_user_not_found(self):
        with self.assertRaises(ValueError):
            UserService.update_user_by_id("non_existing_user_id", {"username": "UpdatedUser"})

    def test_get_user_by_invalid_id(self):
        user = UserService.get_user_by_id("invalid_object_id_format")
        self.assertIsNone(user)


if __name__ == '__main__':
    unittest.main()
