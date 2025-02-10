import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField, ListField

class Announcement(Document):
    title_tr = StringField(required=True, max_length=255)  # Başlık
    title_en = StringField(required=True, max_length=255)  # Başlık
    content_tr = StringField(required=True)  # İçerik
    content_en = StringField(required=True)  # İçerik
    created_at = DateTimeField(default=datetime.datetime.utcnow)  # Oluşturulma Tarihi
    image_url = StringField(max_length=1024)  # Görsel URL (Opsiyonel)
    video_url = StringField(max_length=1024)  # Video URL (Opsiyonel)
    is_published = BooleanField(default=True)  # Yayın Durumu
    tags = ListField(StringField(max_length=50))  # Etiketler

    meta = {
        'db_alias' : "default",
        'collection': 'announcements',  # Veritabanı koleksiyon adı
        'ordering': ['-created_at'],  # Varsayılan sıralama
    }

    def __str__(self):
        return f"{self.title} - Published: {self.is_published}"
