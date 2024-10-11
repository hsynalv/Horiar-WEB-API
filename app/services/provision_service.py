from app.models.provision_model import Provision
from app.services.base_service import BaseService


class ProvisionService(BaseService):
    model = Provision

    @staticmethod
    def get_provision_by_merchant_oid(merchant_oid):
        """
        Verilen merchant_oid'ye göre bir provizyon kaydını döndürür.
        """
        try:
            provision = Provision.objects(merchant_oid=merchant_oid).first()
            if provision:
                return provision
            else:
                print(f"Merchant OID {merchant_oid} ile ilgili provizyon kaydı bulunamadı.")
                return None
        except Exception as e:
            print(f"Provizyon kaydı alınırken hata oluştu: {str(e)}")
            return None