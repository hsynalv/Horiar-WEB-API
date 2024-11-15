from mongoengine import Document, StringField, FloatField, ReferenceField, DateTimeField
from datetime import datetime
from app.models.user_model import User  # Kullanıcı modelini eklemek için uygun yolu kullanın
from app.models.package_model import Package  # Paket modelini eklemek için uygun yolu kullanın

class Purchase(Document):
    username = StringField(User, required=True)  # Satın alımı yapan kullanıcı
    package = StringField(Package, required=True)  # Satın alınan paket
    amount = FloatField(required=True)  # Satın alım tutarı (gelir)
    payment_date = DateTimeField(default=datetime.utcnow)  # Satın alımın gerçekleştiği tarih

    meta = {'collection': 'purchases'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": str(self.user.id) if self.user else None,
            "package": str(self.package.id) if self.package else None,
            "amount": self.amount,
            "payment_date": self.payment_date.isoformat(),
        }
