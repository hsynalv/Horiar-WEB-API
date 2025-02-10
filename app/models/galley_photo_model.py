from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField, FloatField, ListField


class GalleryPhoto(Document):
    user_id = StringField(required=True)  # Hangi kullanıcı tarafından oluşturulduğunu belirtir
    username = StringField()  # Kullanıcının adı (opsiyonel)
    title = StringField(required=True)  # Görselin başlığı
    description = StringField()  # Görselin açıklaması (opsiyonel)
    prompt = StringField(required=True)  # Görseli oluşturmak için kullanılan prompt
    image_url = StringField(required=True)  # Görselin URL'si
    image_url_webp = StringField()  # WebP formatındaki URL (optimizasyon için)
    created_at = DateTimeField(required=True)  # Görselin oluşturulma tarihi
    is_visible = BooleanField(default=True)  # Görselin galeride görünüp görünmeyeceği
    likes_count = IntField(default=0)  # Görselin kaç beğeni aldığı
    views_count = IntField(default=0)  # Görselin kaç kez görüntülendiği
    tags = ListField(StringField())  # Görselle ilgili etiketler (virgülle ayrılmış şekilde)
    liked_by_users = ListField(StringField())  # Beğenen kullanıcıların user_id'lerini tutar
    model_type = StringField()
    prompt_fix = StringField()
    resolution = StringField()

    meta = {
        'db_alias': "default",
        'collection': 'gallery',
        'indexes': [
            'user_id',
            'created_at',
            'is_visible',
            'tags'
        ]
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "image_url": self.image_url,
            "image_url_webp": self.image_url_webp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_visible": self.is_visible,
            "likes_count": self.likes_count,
            "views_count": self.views_count,
            "tags": self.tags,
            "liked_by_users": self.liked_by_users,
            "model_type": self.model_type,
            "prompt_fix": self.prompt_fix,
            "resolution": self.resolution
        }

    def to_dict_for_frontend(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "username": self.username,
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "image": self.image_url_webp,
            "likes_count": self.likes_count,
            "views_count": self.views_count,
            "tags": self.tags,
            "liked_by_users": self.liked_by_users,
            "model_type": self.model_type,
            "prompt_fix": self.prompt_fix,
            "resolution": self.resolution
        }
