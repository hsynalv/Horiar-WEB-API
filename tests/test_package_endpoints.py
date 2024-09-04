import unittest
from app import create_app

class TestPackageEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_add_package_success(self):
        response = self.client.post('/package/packages', json={
            "name": "Premium Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 12
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("Package added successfully", response.get_json()["message"])

    def test_add_package_missing_fields(self):
        response = self.client.post('/package/packages', json={
            "credits": 200,
            "price": 15
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.get_json()["message"])

    def test_add_package_invalid_discount(self):
        response = self.client.post('/package/packages', json={
            "name": "Premium Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 20  # İndirimli fiyat normal fiyattan büyük
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Discounted price cannot be greater than the original price.", response.get_json()["message"])

    def test_get_package_success(self):
        add_response = self.client.post('/package/packages', json={
            "name": "Standard Package",
            "credits": 150,
            "price": 12,
            "discounted_price": 10
        })
        package_id = add_response.get_json()["package_id"]

        response = self.client.get(f'/package/packages/{package_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Standard Package", response.get_json()["name"])

    def test_update_package_success(self):
        add_response = self.client.post('/package/packages', json={
            "name": "Basic Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })
        package_id = add_response.get_json()["package_id"]

        response = self.client.put(f'/package/packages/{package_id}', json={
            "name": "Updated Package",
            "credits": 200,
            "price": 15,
            "discounted_price": 10
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Package updated successfully", response.get_json()["message"])

    def test_delete_package_success(self):
        add_response = self.client.post('/package/packages', json={
            "name": "Delete Package",
            "credits": 100,
            "price": 10,
            "discounted_price": 8
        })
        package_id = add_response.get_json()["package_id"]

        response = self.client.delete(f'/package/packages/{package_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Package deleted successfully", response.get_json()["message"])
