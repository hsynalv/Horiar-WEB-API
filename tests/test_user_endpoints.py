import unittest
from app import create_app

class TestUserEndpoints(unittest.TestCase):

    def setUp(self):
        # Flask uygulamasını oluştur ve test client'ı başlat
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Uygulama bağlamını başlat
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Testler bittikten sonra bağlamı temizle
        self.app_context.pop()

    def test_signup_success(self):
        # Başarılı kullanıcı kayıt işlemi
        response = self.client.post('/user/signup', json={
            "email": "newuser@example.com",
            "password": "password123",
            "username": "NewUser"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.get_json()["message"])

    def test_signup_missing_fields(self):
        # Eksik alanlarla kayıt denemesi
        response = self.client.post('/user/signup', json={
            "email": "newuser@example.com",
            "password": ""
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])

    def test_login_success(self):
        # Başarılı giriş işlemi (önce bir kullanıcı oluşturuyoruz)
        self.client.post('/user/signup', json={
            "email": "loginuser@example.com",
            "password": "password123",
            "username": "LoginUser"
        })

        # Şimdi giriş yapmayı test edelim
        response = self.client.post('/user/login', json={
            "email": "loginuser@example.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.get_json()["message"])

    def test_login_invalid_credentials(self):
        # Yanlış şifre ile giriş denemesi
        response = self.client.post('/user/login', json={
            "email": "loginuser@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_json()["message"])

    def test_signup_duplicate_email(self):
        # Aynı email ile iki kez kayıt olmaya çalışalım
        self.client.post('/user/signup', json={
            "email": "duplicateuser@example.com",
            "password": "password123",
            "username": "DuplicateUser"
        })

        response = self.client.post('/user/signup', json={
            "email": "duplicateuser@example.com",
            "password": "password123",
            "username": "DuplicateUser"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("User already exists", response.get_json()["message"])

"""
    def test_access_protected_route_with_invalid_token(self):
        # Geçersiz bir token ile korumalı bir rotaya erişim denemesi
        response = self.client.get('/user/protected_route', headers={
            "Authorization": "Bearer invalid_token"
        })
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is invalid or expired", response.get_json()["message"])
"""


