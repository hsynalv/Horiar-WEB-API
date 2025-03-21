from mongoengine.fields import StringField, IntField, FloatField, DictField
from flask_mongoengine import Document

class Package(Document):
    title = StringField(required=True, max_length=100)  # Eski 'name' alanı 'title' olarak güncellendi
    monthly_original_price = FloatField(required=True)  # Aylık orijinal fiyat
    yearly_original_price = FloatField(required=True)  # Yıllık orijinal fiyat
    monthly_sale_price = FloatField(required=False)  # Aylık indirimli fiyat (opsiyonel)
    yearly_sale_price = FloatField(required=False)  # Yıllık indirimli fiyat (opsiyonel)
    credits = IntField(required=True)

    features = DictField(
        required=True,
        default=lambda: {
            'en': {
                'feature_1': '',
                'feature_2': ''
            },
            'tr': {
                'feature_1': '',
                'feature_2': ''
            }
        }
    )

    meta = {
        'db_alias' : "default",
        'collection': 'packages'
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "monthlyOriginalPrice": self.monthly_original_price,
            "yearlyOriginalPrice": self.yearly_original_price,
            "monthlySalePrice": self.monthly_sale_price,
            "yearlySalePrice": self.yearly_sale_price,
            "features": self.features,
            "credits": self.credits,
        }
