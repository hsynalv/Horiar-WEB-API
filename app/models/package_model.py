class Package:
    def __init__(self, name, credits, price, discounted_price=None, _id=None):
        self._id = _id  # Veritabanından gelen _id'yi burada saklayacağız
        self.name = name
        self.credits = credits
        self.price = price
        self.discounted_price = discounted_price if discounted_price is not None else price

    def to_dict(self):
        package_dict = {
            "name": self.name,
            "credits": self.credits,
            "price": self.price,
            "discounted_price": self.discounted_price
        }

        if self._id:
            package_dict["_id"] = str(self._id)  # _id varsa onu da ekleyelim

        return package_dict

    @staticmethod
    def from_dict(data):
        return Package(
            name=data.get("name"),
            credits=data.get("credits"),
            price=data.get("price"),
            discounted_price=data.get("discounted_price"),
            _id=data.get("_id")  # Veritabanından dönen _id'yi de alabiliriz
        )
