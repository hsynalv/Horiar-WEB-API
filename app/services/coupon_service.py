# /app/services/coupon_service.py
from app.models.coupon_model import Coupon
from app.models.user_model import User
from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError
from app.services.base_service import BaseService

class CouponService(BaseService):
    model = Coupon

    @staticmethod
    def use_coupon(coupon_name, user_id):
        coupon = Coupon.objects(name=coupon_name).first()
        if not coupon:
            raise NotFoundError("Coupon not found")
        print("serviste kupon bulundu")

        if coupon.usage_count >= coupon.max_usage:
            raise ValidationError("Coupon has reached its maximum usage limit")

        # Kuponu kullanan kullanıcıyı bul
        user = User.objects(id=user_id).first()
        print("serviste user bulundu")
        if not user:
            raise NotFoundError("User not found")

        if user in coupon.used_by:
            raise ValidationError("User has already used this coupon")

        print("serviste kullanım detayı öncesi")

        # Kupon kullanım sayısını arttır
        coupon.usage_count += 1
        coupon.used_by.append(user)
        coupon.save()

        print("servis return öncesi")

        return coupon.to_dict()

    @staticmethod
    def add_coupon(data):
        if not data.get("name") or not data.get("discount_percentage") or not data.get("valid_until") or not data.get(
                "max_usage"):
            raise ValueError("Missing required fields")  # max_usage alanının zorunlu olduğunu kontrol ediyoruz

        coupon = Coupon(**data)
        coupon.save()

        return str(coupon.id)
