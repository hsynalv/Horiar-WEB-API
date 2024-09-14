# /app/services/coupon_service.py
from app.models.coupon_model import Coupon
from app.models.user_model import User
from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError
from app.services.base_service import BaseService

class CouponService(BaseService):
    model = Coupon

    @staticmethod
    def use_coupon(coupon_id, user_id):
        coupon = Coupon.objects(id=coupon_id).first()
        if not coupon:
            raise NotFoundError("Coupon not found")

        if coupon.usage_count >= coupon.max_usage:
            raise ValidationError("Coupon has reached its maximum usage limit")

        # Kuponu kullanan kullanıcıyı ekle
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError("User not found")

        if user in coupon.used_by:
            raise ValidationError("User has already used this coupon")

        # Kupon kullanım sayısını arttır
        coupon.usage_count += 1
        coupon.used_by.append(user)
        coupon.save()

        return coupon.to_dict()

    @staticmethod
    def add_coupon(data):
        if not data.get("name") or not data.get("discount_percentage") or not data.get("valid_until") or not data.get(
                "max_usage"):
            raise ValueError("Missing required fields")  # max_usage alanının zorunlu olduğunu kontrol ediyoruz

        coupon = Coupon(**data)
        coupon.save()

        return str(coupon.id)
