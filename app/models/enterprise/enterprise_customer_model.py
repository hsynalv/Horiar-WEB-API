from flask_mongoengine import Document
from mongoengine import StringField, BooleanField, DateTimeField, IntField
import datetime


class EnterpriseCustomer(Document):
    """
    Enterprise müşteri modelini tanımlar.
    """
    # Müşteriyle ilgili temel bilgiler
    company_name = StringField(required=True, max_length=255)  # Şirketin adı
    contact_email = StringField(required=True, unique=True)  # Müşteri için iletişim e-postası
    created_at = DateTimeField(default=datetime.datetime.utcnow)  # Müşteri kaydının oluşturulma tarihi
    api_key = StringField(required=False, unique=True, max_length=64)  # API anahtarı

    ## API kullanımı ile ilgili bilgiler
    #plan_type = StringField(required=True, choices=('basic', 'pro', 'enterprise'))  # Müşteri planı (enterprise için)
    #usage_limit = IntField(default=10000)  # Kullanım sınırı (API istek sayısı gibi)
    ## Müşteri durumu
    #is_active = BooleanField(default=True)  # Müşteri hesabının aktif olup olmadığını kontrol eder
    #last_login = DateTimeField()  # Müşterinin son giriş yaptığı tarih

    meta = {'collection': 'enterprise_customers'}  # MongoDB'de toplanacağı koleksiyon ismi

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat(),
            "api_key": self.api_key
            #"plan_type": self.plan_type,
            #"usage_limit": self.usage_limit,
            #"is_active": self.is_active,
            #"last_login": self.last_login.isoformat() if self.last_login else None
        }
