from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError
from app.models.package_model import Package
from app.services.base_service import BaseService

class PackageService(BaseService):
    model = Package

    @staticmethod
    def validate_discount(original_price, discounted_price):
        if discounted_price and discounted_price > original_price:
            raise ValidationError("Discounted price cannot be greater than the original price")

    @staticmethod
    def validate_features(features):
        if not isinstance(features, dict):
            raise ValidationError("Features must be a dictionary")
        if 'en' not in features or 'tr' not in features:
            raise ValidationError("Features must contain both 'en' and 'tr' keys")
        # Her iki dildeki özelliklerin de listelenmiş olup olmadığını kontrol et
        if not isinstance(features['en'], dict) or not isinstance(features['tr'], dict):
            raise ValidationError("Both 'en' and 'tr' keys must contain a dictionary of features")

    @staticmethod
    def add_package(data):
        # Eksik alan kontrolü
        required_fields = ["title", "monthly_original_price", "yearly_original_price", "features", "credits"]
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        # İndirimli fiyat kontrolü
        if data.get('monthly_sale_price'):
            PackageService.validate_discount(data.get('monthly_original_price'), data.get('monthly_sale_price'))
        if data.get('yearly_sale_price'):
            PackageService.validate_discount(data.get('yearly_original_price'), data.get('yearly_sale_price'))

        # Features alanını kontrol et
        PackageService.validate_features(data['features'])

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
        if data.get('monthly_sale_price'):
            PackageService.validate_discount(data.get('monthly_original_price'), data.get('monthly_sale_price'))
        if data.get('yearly_sale_price'):
            PackageService.validate_discount(data.get('yearly_original_price'), data.get('yearly_sale_price'))

        # Features alanı güncelleniyorsa kontrol et
        if data.get('features'):
            PackageService.validate_features(data['features'])

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
