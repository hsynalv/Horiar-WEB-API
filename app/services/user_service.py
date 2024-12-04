import logging
import uuid
from itertools import chain

from mongoengine.errors import NotUniqueError
from mongoengine import NotUniqueError
from pymongo.errors import DuplicateKeyError

from app.errors.not_found_error import NotFoundError
from app.models.image_to_video_model import ImageToVideo
from app.models.text_to_image_model import TextToImage
from app.models.text_to_video_model import TextToVideoGeneration
from app.models.upscale_model import Upscale
from app.models.user_model import User
from passlib.hash import pbkdf2_sha256  # passlib ile pbkdf2_sha256 kullanımı
import re
import datetime

from app.services.base_service import BaseService
from app.services.subscription_service import SubscriptionService


class UserService(BaseService):
    model = User

    @staticmethod
    def add_or_update_user(user_data):
        """
        Kullanıcıyı ekler veya günceller.
        """
        user = UserService.model.objects(email=user_data["email"]).first()

        if user:
            if user_data.get("google_id"):
                user.google_id = user_data["google_id"]
                user.google_username = user_data["google_username"]
            elif user_data.get("discord_id"):
                user.discord_id = user_data["discord_id"]
                user.discord_username = user_data["discord_username"]

            # Son giriş tarihini güncelle
            user.last_login_date = datetime.datetime.utcnow()
            user.save()  # Değişiklikleri kaydetmek için save() kullanılır
        else:
            user_data["registration_date"] = datetime.datetime.utcnow()
            user = User(**user_data)
            user.save()

        return user  # Artık user id yerine tüm user nesnesini döndürüyoruz

    @staticmethod
    def find_user_by_email(email):
        """
        E-posta ile kullanıcıyı bulur.
        """
        email = email.lower()
        return User.objects(email=email).first()

    @staticmethod
    def check_password(stored_password, provided_password):
        """
        Kullanıcının şifresini doğrular. pbkdf2_sha256 kullanılıyor.
        """
        if stored_password is None:
            raise ValueError("Kullanıcının şifresi yok")  # Şifre yoksa hata fırlat
        return pbkdf2_sha256.verify(provided_password, stored_password)

    @staticmethod
    def add_user(email, password):
        """
        Yeni bir kullanıcı ekler. Kullanıcı adı rastgele oluşturulur.
        """
        try:
            # Kullanıcı verilerini doğrula

            email = email.lower()
            UserService.validate_user_data(email, password)

            # Rastgele kullanıcı adı oluştur
            random_username = f"user_{uuid.uuid4().hex[:8]}"  # 8 karakterlik rastgele bir kullanıcı adı

            # Benzersiz bir kullanıcı adı oluşturulana kadar kontrol et
            while User.objects(username=random_username).first():
                random_username = f"user_{uuid.uuid4().hex[:8]}"

            # Şifreyi hash'le ve kullanıcıyı ekle (pbkdf2_sha256 kullanılıyor)
            hashed_password = pbkdf2_sha256.hash(password)
            user = User(email=email, username=random_username, password=hashed_password)
            user.save()

            return str(user.id)

        except DuplicateKeyError as e:
            logging.error(f"Duplicate key error while adding user: {e}")
            raise ValueError("Bu email adresi ile zaten kayıtlı bir kullanıcı mevcut.")

        except NotUniqueError as e:
            logging.error(f"Not unique error while adding user: {e}")
            raise ValueError("Bu email adresi veya kullanıcı adı zaten mevcut.")

        except Exception as e:
            logging.error(f"Unhandled exception while adding user: {e}")
            raise ValueError("User with this email already exists")

    @staticmethod
    def get_user_by_id(user_id):
        """
        Kullanıcıyı ID'ye göre getirir. Eğer kullanıcı bulunamazsa hata fırlatır.
        """
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        return user

    @staticmethod
    def update_user_by_id(user_id, update_data):
        """
        Kullanıcıyı ID ile günceller.
        """
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        user.update(**update_data)

    @staticmethod
    def validate_user_data(email, password):
        """
        Kullanıcı oluşturma verilerini doğrular.
        """
        if not email or not password:
            raise ValueError("Missing required fields")

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")


        # E-posta var mı kontrol et
        existing_user_email = User.objects(email=email).first()
        if existing_user_email:
            raise ValueError("User with this email already exists")

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Kullanıcının şifresini değiştirir.
        """
        # Kullanıcıyı al
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        # Mevcut şifreyi doğrula
        if not pbkdf2_sha256.verify(current_password, user.password):
            raise ValueError("Current password is incorrect")

        # Yeni şifreyi hash'le ve güncelle
        user.password = pbkdf2_sha256.hash(new_password)
        user.save()

    @staticmethod
    def get_all_users():
        """
        Tüm kullanıcıları döndürür.
        """
        return User.objects().all()

    @staticmethod
    def get_user_credit(user_id):
        subscription = SubscriptionService.get_subscription_by_id(user_id)

        if subscription:
            return {
                    "currentCredit": int(subscription.credit_balance),
                    "maxCredit":int(subscription.max_credit_balance)
            }

        user = UserService.get_user_by_id(user_id)
        return {
                    "currentCredit": int(user.base_credits),
                    "maxCredit": 15
        }

    @staticmethod
    def get_all_requests(payload, page=1, page_size=10):
        user_id = payload.get("sub")
        logging.info(user_id)

        # Farklı render türlerinden verileri çekiyoruz, sadece istenen alanları belirtiyoruz
        text_to_image_renders = TextToImage.objects(user_id=user_id).only(
            "datetime", "prompt", "seed", "model_type", "prompt_fix", "resolution", "image_url", "image_url_webp", "consistent"
        )

        image_to_video_renders = ImageToVideo.objects(user_id=user_id).only(
            "prompt", "image_url", "video_url", "datetime"
        )

        upscale_renders = Upscale.objects(user_id=user_id).only(
            "datetime", "low_res_image_url", "high_res_image_url", "image_url_webp"
        )

        text_to_video_renders = TextToVideoGeneration.objects(user_id=user_id).only(
            "prompt", "video_url", "datetime"
        )

        logging.info(f"text to image count: {text_to_image_renders.count()}")
        logging.info(f"image_to_video_generation_renders count: {image_to_video_renders.count()}")
        logging.info(f"upscale_renders count: {upscale_renders.count()}")
        logging.info(f"text_to_video_renders count: {text_to_video_renders.count()}")

        # Tüm renderları birleştiriyoruz ve her rendera type bilgisi ekliyoruz
        all_renders = chain(
            [(render, "Text to Image") for render in text_to_image_renders],
            [(render, "Image to Video") for render in image_to_video_renders],
            [(render, "Upscale") for render in upscale_renders],
            [(render, "Text to Video") for render in text_to_video_renders]
        )

        # Renderları tarihe göre sıralıyoruz (azalan)
        sorted_renders = sorted(all_renders, key=lambda r: r[0].datetime, reverse=True)

        # Sayfalama işlemi
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_renders = sorted_renders[start_index:end_index]

        # JSON formatına dönüştürüyoruz
        render_list = []
        for render, render_type in paginated_renders:
            render_data = {
                "created_at": render.datetime.isoformat(),
                "type": render_type,  # Type bilgisi elle ekleniyor
                "data": render.to_dict_frontend()
            }
            render_list.append(render_data)

        return render_list