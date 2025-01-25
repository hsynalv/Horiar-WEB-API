from datetime import datetime

from app.models.subscription_model import Subscription
from app.services.base_service import BaseService


class SubscriptionService(BaseService):
    model = Subscription

    @staticmethod
    def get_subscription_by_id(user_id):
        """
        Verilen user_id'ye göre bir subscription kaydını döndürür.
        """
        try:
            # Bugünün tarihini al
            today = datetime.utcnow()

            # Tarihi bugünden sonra olan kayıtları getir
            subscription = Subscription.objects(
                user_id=user_id,
                subscription_end_date__gte=today  # Tarih bugünden büyük veya eşit olanlar
            ).first()

            if subscription:
                return subscription
            else:
                print(f"User ID {user_id} ile ilgili bir subscription kaydı bulunamadı.")
                return None
        except Exception as e:
            print(f"Subscription kaydı alınırken hata oluştu: {str(e)}")
            return None