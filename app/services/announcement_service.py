import os
from io import BytesIO

import openai

from app.models.announcement_model import Announcement
from app.services.base_service import BaseService
from app.utils.convert_to_webp import upload_image_to_s3

openai.api_key = os.getenv("OPEN_AI_KEY")

class AnnouncementService(BaseService):
    model = Announcement
    Duty_Translate = "You are a translator GPT, your job is to translate the {text} from any language to English without any changes in the context. Be straightforward and direct for the translation"


    @staticmethod
    def translatePrompt(text):
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{AnnouncementService.Duty_Translate}"},
                {"role": "user", "content": f"text: {text}"}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        result = response.choices[0].message.content

        # 'Text: ' veya 'text: ' ile başlıyorsa bunu çıkarıyoruz
        if result.lower().startswith("text: "):
            result = result[6:]  # "Text: " veya "text: " kısmını kaldır

        return result

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

        title_en = AnnouncementService.translatePrompt(title)
        content_en = AnnouncementService.translatePrompt(content)

        announcement = Announcement(
            title_tr=title.title(),
            title_en=title_en.title(),
            content_tr=content,
            content_en=content_en,
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