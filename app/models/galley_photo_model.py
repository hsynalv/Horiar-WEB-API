from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField, FloatField

class GalleryPhoto(Document):
    id = StringField(primary_key=True, required=True)
    user_id = StringField(required=True)  # Hangi kullanıcı tarafından oluşturulduğunu belirtir
    user_name = StringField()  # Kullanıcının adı (opsiyonel)
    title = StringField(required=True)  # Görselin başlığı
    description = StringField()  # Görselin açıklaması (opsiyonel)
    prompt = StringField(required=True)  # Görseli oluşturmak için kullanılan prompt
    image_url = StringField(required=True)  # Görselin URL'si
    image_url_webp = StringField()  # WebP formatındaki URL (optimizasyon için)
    created_at = DateTimeField(required=True)  # Görselin oluşturulma tarihi
    is_visible = BooleanField(default=True)  # Görselin galeride görünüp görünmeyeceği
    likes_count = IntField(default=0)  # Görselin kaç beğeni aldığı
    views_count = IntField(default=0)  # Görselin kaç kez görüntülendiği
    execution_time = FloatField()  # Görselin oluşturulma süresi (isteğe bağlı)
    cost = FloatField()  # Görselin oluşturulma maliyeti (isteğe bağlı)
    tags = StringField()  # Görselle ilgili etiketler (virgülle ayrılmış şekilde)

    meta = {
        'collection': 'text_to_image_gallery',
        'indexes': [
            'user_id',
            'created_at',
            'is_visible',
            'tags'
        ]
    }

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "image_url": self.image_url,
            "image_url_webp": self.image_url_webp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_visible": self.is_visible,
            "likes_count": self.likes_count,
            "views_count": self.views_count,
            "execution_time": self.execution_time,
            "cost": self.cost,
            "tags": self.tags
        }
