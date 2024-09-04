import unittest
from app import create_app

class TestUserEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        # Her testten önce veritabanını temizle
        self.app.db["users"].delete_many({})

    def tearDown(self):
        self.app_context.pop()

    def test_signup_success(self):
        response = self.client.post('/user/signup', json={
            "email": "newuser@example.com",
            "password": "password123",
            "username": "NewUser"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.get_json()["message"])

    def test_signup_missing_fields(self):
        response = self.client.post('/user/signup', json={
            "email": "newuser@example.com",
            "password": ""
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])

    def test_login_success(self):
        # Kullanıcı oluştur
        self.client.post('/user/signup', json={
            "email": "loginuser@example.com",
            "password": "password123",
            "username": "LoginUser"
        })

        # Giriş yap
        response = self.client.post('/user/login', json={
            "email": "loginuser@example.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.get_json()["message"])

    def test_login_invalid_credentials(self):
        response = self.client.post('/user/login', json={
            "email": "loginuser@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_json()["message"])

    def test_get_user_by_id_success(self):
        # Kullanıcı oluştur
        signup_response = self.client.post('/user/signup', json={
            "email": "userbyid@example.com",
            "password": "password123",
            "username": "UserById"
        })
        user_id = signup_response.get_json()["user_id"]

        # ID ile kullanıcıyı getir
        response = self.client.get(f'/user/getuser/{user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "userbyid@example.com")

    def test_get_user_by_id_not_found(self):
        response = self.client.get('/user/getuser/invalid_user_id')
        self.assertEqual(response.status_code, 404)
        self.assertIn("User not found", response.get_json()["message"])

    def test_signup_existing_email(self):
        # İlk kullanıcıyı ekle
        self.client.post('/user/signup', json={
            "email": "duplicateuser@example.com",
            "password": "password123",
            "username": "FirstUser"
        })

        # Aynı email ile tekrar kayıt olma denemesi
        response = self.client.post('/user/signup', json={
            "email": "duplicateuser@example.com",
            "password": "password123",
            "username": "SecondUser"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("User already exists", response.get_json()["message"])

    def test_login_non_existent_user(self):
        # Var olmayan kullanıcı ile giriş denemesi
        response = self.client.post('/user/login', json={
            "email": "nonexistentuser@example.com",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_json()["message"])

    def test_protected_route_no_token(self):
        response = self.client.get('/user/protected-route')  # JWT gerektiren bir route
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is missing!", response.get_json()["message"])

    def test_protected_route_invalid_token(self):
        response = self.client.get('/user/protected-route', headers={
            "Authorization": "Bearer invalid_token"
        })
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is invalid or expired!", response.get_json()["message"])


if __name__ == '__main__':
    unittest.main()
