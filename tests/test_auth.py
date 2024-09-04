import unittest
import jwt
import datetime
from flask import Flask, jsonify
from app.auth import create_jwt_token, verify_jwt_token, jwt_required
import uuid

class TestAuth(unittest.TestCase):

    def setUp(self):
        # Flask uygulamasını ve test client'ını oluştur
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

        # Test edilen rota
        @self.app.route('/protected')
        @jwt_required
        def protected_route(payload):
            return jsonify({"message": "Access granted", "user_id": payload["sub"]})

        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # create_jwt_token Testleri
    def test_create_jwt_token(self):
        token = create_jwt_token("user_id_123", "TestUser", self.app.config['SECRET_KEY'])
        decoded_token = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=["HS256"], audience='horiar_client')

        self.assertEqual(decoded_token["sub"], "user_id_123")
        self.assertEqual(decoded_token["username"], "TestUser")
        self.assertIn("exp", decoded_token)  # Token'da expiration süresi olup olmadığını kontrol et
        self.assertIn("jti", decoded_token)  # Token'da jti olup olmadığını kontrol et

    # verify_jwt_token Testleri
    def test_verify_jwt_token_valid(self):
        token = create_jwt_token("user_id_123", "TestUser", self.app.config['SECRET_KEY'])
        payload = verify_jwt_token(token, self.app.config['SECRET_KEY'])

        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user_id_123")
        self.assertEqual(payload["username"], "TestUser")

    def test_verify_jwt_token_expired(self):
        # Süresi geçmiş bir token oluştur
        expired_token = jwt.encode({
            "sub": "user_id_123",
            "username": "TestUser",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1),
            "aud": "horiar_client",
            "iss": "horiarapi.com",
            "jti": str(uuid.uuid4())
        }, self.app.config['SECRET_KEY'], algorithm="HS256")

        payload = verify_jwt_token(expired_token, self.app.config['SECRET_KEY'])
        self.assertIsNone(payload)

    def test_verify_jwt_token_invalid(self):
        invalid_token = "invalid_token"
        payload = verify_jwt_token(invalid_token, self.app.config['SECRET_KEY'])
        self.assertIsNone(payload)

    # jwt_required Testleri
    def test_protected_route_no_token(self):
        response = self.client.get('/protected')
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is missing!", response.get_json()["message"])

    def test_protected_route_with_valid_token(self):
        token = create_jwt_token("user_id_123", "TestUser", self.app.config['SECRET_KEY'])
        response = self.client.get('/protected', headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access granted", response.get_json()["message"])

    def test_protected_route_with_invalid_token(self):
        response = self.client.get('/protected', headers={"Authorization": "Bearer invalid_token"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is invalid or expired!", response.get_json()["message"])

    def test_verify_jwt_token_with_wrong_secret(self):
        # Yanlış bir secret key ile token oluşturulmuş
        token = create_jwt_token("user_id_123", "TestUser", "wrong_secret_key")
        payload = verify_jwt_token(token, self.app.config['SECRET_KEY'])

        # Doğru secret key kullanarak doğrulama yapılmalı, dolayısıyla payload None olmalı
        self.assertIsNone(payload)

    def test_protected_route_with_expired_token(self):
        # Süresi dolmuş bir token oluştur
        expired_token = jwt.encode({
            "sub": "user_id_123",
            "username": "TestUser",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1),
            "aud": "horiar_client",
            "iss": "horiarapi.com",
            "jti": str(uuid.uuid4())
        }, self.app.config['SECRET_KEY'], algorithm="HS256")

        # Süresi dolmuş token ile korunan route'a erişim
        response = self.client.get('/protected', headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is invalid or expired!", response.get_json()["message"])

    def test_jwt_token_with_missing_user_id(self):
        # user_id eksik token oluştur
        token = jwt.encode({
            "username": "TestUser",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=30),
            "aud": "horiar_client",
            "iss": "horiarapi.com",
            "jti": str(uuid.uuid4())
        }, self.app.config['SECRET_KEY'], algorithm="HS256")

        payload = verify_jwt_token(token, self.app.config['SECRET_KEY'])

        # user_id eksik olduğundan doğrulama None dönmeli
        self.assertIsNone(payload)

    def test_protected_route_with_tampered_token(self):
        token = create_jwt_token("user_id_123", "TestUser", self.app.config['SECRET_KEY'])

        # Token'ı değiştirerek imzasını boz
        tampered_token = token[:-5] + "12345"

        response = self.client.get('/protected', headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Token is invalid or expired!", response.get_json()["message"])


if __name__ == '__main__':
    unittest.main()
