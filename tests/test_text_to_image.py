import unittest
from unittest.mock import patch, MagicMock
from queue import Queue
from app.services.text_to_image_service import TextToImageService, image_queue, is_processing
from flask import Flask
from app import create_app

class TestTextToImageService(unittest.TestCase):

    def setUp(self):
        # Flask uygulamasını oluştur ve test için bağlamını başlat
        self.app = create_app()
        self.app.config['TESTING'] = True

        # Uygulama bağlamı
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Testler bittikten sonra uygulama bağlamını temizle
        self.app_context.pop()
        image_queue.queue.clear()  # Kuyruğu temizle
        global is_processing
        is_processing = False

    @patch("app.services.text_to_image.TextToImageService.update_workflow_with_prompt")
    @patch("app.services.text_to_image.requests.post")
    def test_generate_image_from_text(self, mock_post, mock_update_workflow):
        # Mock workflow güncelleme işlemi
        mock_update_workflow.return_value = {"workflow": "mocked workflow data"}

        # Mock RunPod API yanıtı
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"image_url": "http://example.com/image.png"}
        mock_post.return_value = mock_response

        # Prompt kullanarak görüntü oluşturma işlemini test et
        result = TextToImageService.generate_image_from_text(self.app, "Test prompt")
        self.assertIsNotNone(result)
        self.assertEqual(result["image_url"], "http://example.com/image.png")

    @patch("app.services.text_to_image.TextToImageService.generate_image_from_text")
    def test_add_to_queue(self, mock_generate_image):
        # Mock generate_image_from_text fonksiyonu
        mock_generate_image.return_value = {"image_url": "http://example.com/image.png"}

        # Kuyruğa ekleyelim
        result = TextToImageService.add_to_queue(self.app, "Test prompt")
        self.assertIsNotNone(result)
        self.assertEqual(result["image_url"], "http://example.com/image.png")
        self.assertEqual(image_queue.qsize(), 0)  # Kuyruk boş olmalı çünkü işlem tamamlandı

    @patch("app.services.text_to_image.TextToImageService.generate_image_from_text")
    def test_process_queue(self, mock_generate_image):
        # Mock generate_image_from_text fonksiyonu
        mock_generate_image.return_value = {"image_url": "http://example.com/image.png"}

        # Kuyruğa birden fazla öğe ekleyelim
        TextToImageService.add_to_queue(self.app, "Prompt 1")
        TextToImageService.add_to_queue(self.app, "Prompt 2")

        # Kuyruğun doğru işlendiğini kontrol edelim
        TextToImageService.process_queue()
        self.assertEqual(image_queue.qsize(), 0)  # Kuyruk boş olmalı
        self.assertFalse(is_processing)  # İşlem tamamlanmış olmalı

    @patch("app.services.text_to_image.requests.post")
    def test_generate_image_from_text_api_failure(self, mock_post):
        # Mock API yanıtı (başarısız istek)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):  # Hata beklentisi
            TextToImageService.generate_image_from_text(self.app, "Test prompt")

    @patch("app.services.text_to_image.TextToImageService.generate_image_from_text")
    def test_queue_processing_order(self, mock_generate_image):
        # Mock generate_image_from_text fonksiyonu
        mock_generate_image.side_effect = [{"image_url": "http://example.com/image1.png"},
                                           {"image_url": "http://example.com/image2.png"}]

        # Kuyruğa iki öğe ekleyelim
        result1 = TextToImageService.add_to_queue(self.app, "Prompt 1")
        result2 = TextToImageService.add_to_queue(self.app, "Prompt 2")

        # Kuyrukta sırasıyla işlem yapıldığını kontrol edelim
        self.assertEqual(result1["image_url"], "http://example.com/image1.png")
        self.assertEqual(result2["image_url"], "http://example.com/image2.png")

    @patch("app.services.text_to_image.TextToImageService.generate_image_from_text")
    @patch("app.services.text_to_image.TextToImageService.update_workflow_with_prompt")
    def test_generate_image_with_empty_prompt(self, mock_update_workflow, mock_generate_image):
        # Mock update_workflow_with_prompt fonksiyonunu devre dışı bırakıyoruz
        mock_update_workflow.return_value = {"workflow": "mocked workflow data"}

        # Mock generate_image_from_text yanıtı
        mock_generate_image.return_value = {"image_url": "http://example.com/image.png"}

        # Boş prompt'u test et
        with self.assertRaises(ValueError):  # Boş prompt'ta hata beklentisi
            TextToImageService.add_to_queue(self.app, "")


if __name__ == '__main__':
    unittest.main()
