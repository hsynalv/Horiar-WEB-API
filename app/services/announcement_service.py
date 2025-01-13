from io import BytesIO

from app.models.announcement_model import Announcement
from app.services.base_service import BaseService
from app.utils.convert_to_webp import upload_image_to_s3


class AnnouncementService(BaseService):
    model = Announcement

    @staticmethod
    def create_announcement(title, content, image_file=None, tags=None, is_published=True):
        """
        Yeni bir duyuru oluşturur.
        """
        image_url = None
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']

        from app import create_app
        app = create_app()
        with app.app_context():
        # Görsel dosyası varsa S3'e yükle
            if image_file:
                try:
                    image_bytes = BytesIO(image_file.read())  # Görsel dosyasını byte olarak oku
                    file_extension = image_file.filename.split('.')[-1]  # Dosya uzantısını al
                    if file_extension.lower() not in allowed_extensions:
                        raise Exception(f"Desteklenmeyen dosya formatı: {file_extension}")
                    image_url = upload_image_to_s3(app, image_bytes, "66e8552e5138b8459904741b", 'S3_FOLDER_ANNOUNCEMENT', file_extension)
                except Exception as e:
                    raise Exception(f"Görsel S3'e yüklenirken bir hata oluştu: {str(e)}")

        announcement = Announcement(
            title=title,
            content=content,
            image_url=image_url,
            tags=tags or [],
            is_published=is_published
        )
        announcement.save()
        return announcement

    @staticmethod
    def update_announcement(announcement_id, **updates):
        """
        Mevcut bir duyuruyu günceller.
        """
        announcement = Announcement.objects(id=announcement_id).first()
        if not announcement:
            raise ValueError(f"Duyuru bulunamadı: {announcement_id}")

        for key, value in updates.items():
            if hasattr(announcement, key):
                setattr(announcement, key, value)

        announcement.save()
        return announcement

    @staticmethod
    def get_announcement(announcement_id):
        """
        Belirtilen ID'ye sahip duyuruyu getirir.
        """
        announcement = Announcement.objects(id=announcement_id).first()
        if not announcement:
            raise ValueError(f"Duyuru bulunamadı: {announcement_id}")

        return announcement

    @staticmethod
    def get_all_announcements(is_published=None):
        """
        Tüm duyuruları getirir. Yayın durumuna göre filtreleme yapılabilir.
        """
        query = Announcement.objects()
        if is_published is not None:
            query = query.filter(is_published=is_published)

        return query.order_by('-created_at')  # En son oluşturulanlar önce gelir