from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError
from app.models.package_model import Package
from app.services.base_service import BaseService

class PackageService(BaseService):
    model = Package

    @staticmethod
    def validate_discount(price, discounted_price):
        if discounted_price and discounted_price > price:
            raise ValidationError("Discounted price is greater than the price")

    @staticmethod
    def add_package(data):
        # Eksik alan kontrolü
        if not data.get("name") or not data.get("credits") or not data.get("price"):
            raise ValueError("Missing required fields")

        # İndirimli fiyat kontrolü
        PackageService.validate_discount(data.get('price'), data.get('discounted_price'))

        # Model kullanarak paket oluşturma
        package = Package(**data)
        package.save()

        return str(package.id)

    @staticmethod
    def update_package(package_id, data):
        # Paket olup olmadığını kontrol et
        package = Package.objects(id=package_id).first()
        if not package:
            raise NotFoundError("Package not found")

        # İndirimli fiyat kontrolü
        PackageService.validate_discount(data.get('price'), data.get('discounted_price'))

        # Paketi güncelleme
        package.update(**data)

    @staticmethod
    def delete_package(package_id):
        package = PackageService.get_by_id(package_id)
        if package:
            package.delete()
            return True
        raise NotFoundError("Package not found")

    @staticmethod
    def get_package_by_id(package_id):
        """
        Paketi ID'ye göre getirir. Eğer paket bulunamazsa hata fırlatır.
        """
        package = Package.objects(id=package_id).first()
        if not package:
            raise NotFoundError("Package not found")

        return package.to_dict()

    @staticmethod
    def get_all_packages():
        """
        Veritabanındaki tüm paketleri döndürür.
        """
        packages = Package.objects()  # Tüm paketleri alır
        return [package.to_dict() for package in packages]  # Her paketi JSON formatına çevirir

