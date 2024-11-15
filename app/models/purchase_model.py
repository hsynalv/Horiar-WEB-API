from mongoengine import Document, StringField, FloatField, ReferenceField, DateTimeField
from datetime import datetime

class Purchase(Document):
    username = StringField(required=True)  # Satın alımı yapan kullanıcı
    package = StringField(required=True)  # Satın alınan paket
    amount = FloatField(required=True)  # Satın alım tutarı (gelir)
    payment_date = DateTimeField(default=datetime.utcnow)  # Satın alımın gerçekleştiği tarih
    currency = StringField(required=False)

    meta = {'collection': 'purchases'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "package": self.package,
            "amount": self.amount,
            "payment_date": self.payment_date.isoformat(),
            "currency": self.currency
        }
