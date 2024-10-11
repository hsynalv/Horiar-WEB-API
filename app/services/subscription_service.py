from app.models.subscription_model import Subscription
from app.services.base_service import BaseService


class SubscriptionService(BaseService):
    model = Subscription