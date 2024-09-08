from datetime import datetime
from bson import ObjectId

class ImageRequest:
    def __init__(self, user_id, username, prompt, image, request_time=None, _id=None):
        self._id = _id  # Veritabanı için ID
        self.user_id = user_id
        self.username = username
        self.prompt = prompt
        self.image = image  # Yeni eklenen image alanı
        self.request_time = request_time or datetime.utcnow()

    def to_dict(self):
        image_request_dict = {
            "user_id": self.user_id,
            "username": self.username,
            "prompt": self.prompt,
            "image": self.image,  # image alanını da sözlüğe ekle
            "request_time": self.request_time
        }

        if self._id:
            image_request_dict["_id"] = str(self._id)

        return image_request_dict

    @staticmethod
    def from_dict(data):
        return ImageRequest(
            user_id=data.get("user_id"),
            username=data.get("username"),
            prompt=data.get("prompt"),
            image=data.get("image"),  # Veriyi alırken image alanını da ekle
            request_time=data.get("request_time"),
            _id=data.get("_id")
        )
