from mongoengine import Document, StringField, DateTimeField, FloatField, IntField


class Subscription(Document):
    subscription_date = DateTimeField(required=True)  # Abonelik başlangıç tarihi
    subscription_end_date = DateTimeField(required=True)  # Abonelik bitiş tarihi
    credit_balance = FloatField(default=0.0)  # Kredi bakiyesi
    discord_id = StringField(required=False)  # Discord ID
    discord_username = StringField(required=False)  # Discord kullanıcı adı
    user_id = StringField(required=True)  # Kullanıcı ID'si
    username = StringField(required=True)  # Kullanıcı adı
    email = StringField(required=True)
    merchant_oid = StringField(required=True)
    max_credit_balance = IntField(default=0.0)
    used_coupon = StringField(required=False)
    package = StringField(required=False)

    meta = {
        'db_alias': "default",
        'collection': 'subscriptions'
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "subscription_date": self.subscription_date,
            "subscription_end_date": self.subscription_end_date,
            "credit_balance": self.credit_balance,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "merchant_oid": self.merchant_oid,
            "max_credit_balance": self.max_credit_balance,
            "used_coupon": self.used_coupon,
            "package": self.package
        }
