import unittest
from app import create_app
from bson import ObjectId

class TestPackageEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Uygulama bağlamını başlat
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Testler bittikten sonra bağlamı temizle
        self.app_context.pop()

    def test_add_package_success(self):
        # Başarılı bir paket ekleme testi
        response = self.client.post('/package/packages', json={
            "name": "Premium Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 12
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("Package added successfully", response.get_json()["message"])

    def test_get_all_packages(self):
        # Önce bir paket ekleyelim
        self.client.post('/package/packages', json={
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })

        # Paketleri getirme işlemi
        response = self.client.get('/package/packages')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.get_json()) > 0)  # En az 1 paket olmalı

    def test_get_package_by_id(self):
        # Paket ekleyelim
        add_response = self.client.post('/package/packages', json={
            "name": "Standard Package",
            "credits": 150,
            "price": 12,
            "discounted_price": 10
        })

        package_id = add_response.get_json()["package_id"]

        # ID ile paketi getirme işlemi
        response = self.client.get(f'/package/packages/{package_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Standard Package")

    def test_update_package_success(self):
        # Paket ekleyelim
        add_response = self.client.post('/package/packages', json={
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })
        package_id = add_response.get_json()["package_id"]

        # Paketi güncelleyelim
        response = self.client.put(f'/package/packages/{package_id}', json={
            "name": "Updated Package",
            "credits": 200,
            "price": 20,
            "discounted_price": 15
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Package updated successfully", response.get_json()["message"])

    def test_add_package_missing_fields(self):
        response = self.client.post('/package/packages', json={
            "credits": 100,
            "price": 10
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])

    def test_update_package_invalid_id(self):
        # Geçersiz bir package_id ile güncelleme yapmaya çalışalım
        response = self.client.put('/package/packages/invalid_id', json={
            "name": "Invalid Update",
            "credits": 200,
            "price": 15,
            "discounted_price": 10
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn("Package not found", response.get_json()["message"])

    def test_delete_package_invalid_id(self):
        # Geçersiz bir package_id ile silme işlemi yapmaya çalışalım
        response = self.client.delete('/package/packages/invalid_id')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Package not found", response.get_json()["message"])

    def test_add_package_with_invalid_discount(self):
        response = self.client.post('/package/packages', json={
            "name": "Premium Package",
            "credits": 200,
            "price": 10,
            "discounted_price": 15  # İndirimli fiyat, normal fiyattan büyük
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Discounted price cannot be greater than the original price", response.get_json()["message"])

    def test_add_package_with_empty_data(self):
        response = self.client.post('/package/packages', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])

    def test_get_deleted_package(self):
        # Paket ekle
        add_response = self.client.post('/package/packages', json={
            "name": "Delete and Get Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })
        package_id = add_response.get_json()["package_id"]

        # Paketi sil
        self.client.delete(f'/package/packages/{package_id}')

        # Silinen paketi getirme denemesi
        response = self.client.get(f'/package/packages/{package_id}')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Package not found", response.get_json()["message"])



