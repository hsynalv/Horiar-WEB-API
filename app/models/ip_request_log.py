from mongoengine import Document, StringField, IntField, DateTimeField
import datetime

class IPRequestLog(Document):
    ip_address = StringField(required=True, unique=True)  # IP adresi
    request_count = IntField(default=0)  # Yapılan istek sayısı
    last_request_time = DateTimeField(default=datetime.datetime.utcnow)  # Son istek zamanı

    meta = {'collection': 'ip_request_logs'}

    def increment_request(self):
        self.request_count += 1
        self.last_request_time = datetime.datetime.utcnow()
        self.save()
