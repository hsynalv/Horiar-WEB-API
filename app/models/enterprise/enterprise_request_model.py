from flask_mongoengine import Document
from mongoengine import StringField, DateTimeField
import datetime

class EnterpriseRequest(Document):
    """
    Model for storing enterprise text-to-image requests.
    """
    company_id = StringField(required=True)
    company_name = StringField(required=True, max_length=255)  # Şirketin adı
    prompt = StringField(required=False)                        # Kullanılan prompt
    image = StringField(required=False)                         # Üretilen yüksek çözünürlüklü resmin URL'si veya yolu
    seed = StringField()                                       # Seed değeri (varsa)
    model_type = StringField()                                 # Kullanılan model tipi
    resolution = StringField()                                 # Görüntü çözünürlüğü
    low_res_url = StringField()                                # Düşük çözünürlüklü resmin URL'si veya yolu
    created_at = DateTimeField(default=datetime.datetime.utcnow) # Oluşturulma tarihi
    request_type = StringField(required=True)

    meta = {'collection': 'enterprise_requests'}  # MongoDB koleksiyonu

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "company_name": self.company_name,
            "prompt": self.prompt,
            "image": self.image,
            "seed": self.seed,
            "model_type": self.model_type,
            "resolution": self.resolution,
            "low_res_url": self.low_res_url,
            "created_at": self.created_at.isoformat(),
            "request_type": self.request_type
        }
