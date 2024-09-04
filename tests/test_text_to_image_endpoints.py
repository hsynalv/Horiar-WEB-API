import unittest
from unittest.mock import patch
from app import create_app

class TestTextToImageEndpoints(unittest.TestCase):

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

    @patch("app.services.text_to_image.TextToImageService.add_to_queue")
    def test_generate_image_success(self, mock_add_to_queue):
        # Mock sonucu
        mock_add_to_queue.return_value = {"image_url": "http://example.com/image.png"}

        # Geçerli bir prompt ile istek gönderme
        response = self.client.post('/create/generate-image', json={
            "prompt": "A beautiful landscape with mountains"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("image_url", response.get_json())
        self.assertEqual(response.get_json()["image_url"], "http://example.com/image.png")

    def test_generate_image_empty_prompt(self):
        # Boş prompt ile istek gönderme
        response = self.client.post('/create/generate-image', json={
            "prompt": ""
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])
