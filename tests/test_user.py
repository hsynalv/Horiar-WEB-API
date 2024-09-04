import unittest
from mongomock import MongoClient
from app.services.user import UserService
from app import create_app
from werkzeug.security import generate_password_hash
from bson import ObjectId


class TestUserService(unittest.TestCase):

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
        self.users_collection = self.db['users']

        # Uygulama bağlamına mock veritabanını ekle
        self.app.db = self.db

    def tearDown(self):
        # Testler bittikten sonra uygulama bağlamını temizle
        self.app_context.pop()

    def test_add_user(self):
        # Kullanıcıyı ekleyelim
        user_id = UserService.add_user("test@example.com", "password123", "TestUser")
        self.assertIsNotNone(user_id)

        # Aynı email ile tekrar kullanıcı eklemeye çalışalım
        duplicate_user_id = UserService.add_user("test@example.com", "password123", "TestUser")
        self.assertIsNone(duplicate_user_id)

    def test_check_password(self):
        # Kullanıcı ekle ve şifreyi kontrol et
        password = "password123"
        hashed_password = generate_password_hash(password)
        result = UserService.check_password(hashed_password, password)
        self.assertTrue(result)

    def test_find_user_by_email(self):
        # Kullanıcı ekle ve sonrasında kullanıcıyı bulmayı test et
        UserService.add_user("find@example.com", "password123", "FindUser")
        user = UserService.find_user_by_email("find@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], "find@example.com")

    def test_find_user_by_email_not_found(self):
        # Var olmayan bir kullanıcıyı bulmaya çalışalım
        user = UserService.find_user_by_email("notfound@example.com")
        self.assertIsNone(user)

    def test_check_password_incorrect(self):
        # Yanlış şifreyle giriş yapmaya çalışalım
        password = "password123"
        hashed_password = generate_password_hash(password)
        result = UserService.check_password(hashed_password, "wrongpassword")
        self.assertFalse(result)

    def test_add_user_password_is_hashed(self):
        # Kullanıcı ekleyelim
        user_id = UserService.add_user("test@example.com", "password123", "TestUser")
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})

        # Kullanıcının şifresinin hashlenip hashlenmediğini kontrol edelim
        self.assertIsNotNone(user)
        self.assertNotEqual(user["password"], "password123")  # Şifrenin düz metin olmadığından emin ol
        self.assertTrue(user["password"].startswith("scrypt"))  # Hash formatı kontrolü

    def test_add_or_update_user(self):
        # Kullanıcı ekle
        user_data = {
            "email": "update@example.com",
            "password": "password123",
            "username": "TestUser"
        }
        user_id = UserService.add_or_update_user(user_data)

        # Kullanıcıyı güncelle
        updated_user_data = {
            "email": "update@example.com",
            "password": "newpassword123",
            "username": "UpdatedUser"
        }
        updated_user_id = UserService.add_or_update_user(updated_user_data)

        # Güncellenen kullanıcıyı kontrol et
        user = self.users_collection.find_one({"_id": ObjectId(user_id)})
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "UpdatedUser")

    def test_get_user_by_id(self):
        # Kullanıcı ekle ve ID ile kullanıcıyı bulmayı test et
        user_id = UserService.add_user("findbyid@example.com", "password123", "FindByIdUser")
        user = UserService.get_user_by_id(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], "findbyid@example.com")

    def test_get_user_by_id_not_found(self):
        # Var olmayan bir ID ile kullanıcı arayalım
        user = UserService.get_user_by_id("invalid_user_id")
        self.assertIsNone(user)

    def test_check_password_incorrect(self):
        # Yanlış şifre ile giriş yapma testi
        hashed_password = generate_password_hash("correctpassword")
        result = UserService.check_password(hashed_password, "wrongpassword")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
