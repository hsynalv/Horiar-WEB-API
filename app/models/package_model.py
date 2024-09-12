from mongoengine import Document, StringField, IntField, FloatField

class Package(Document):
    name = StringField(required=True, max_length=100)
    credits = IntField(required=True)
    price = FloatField(required=True)
    discounted_price = FloatField()

    meta = {'collection': 'packages'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "credits": self.credits,
            "price": self.price,
            "discounted_price": self.discounted_price
        }
