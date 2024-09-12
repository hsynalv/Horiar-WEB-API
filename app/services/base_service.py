class BaseService:
    model = None  # Her alt sınıf bu alanda kendi modelini belirleyecek

    @classmethod
    def get_by_id(cls, id):
        return cls.model.objects(id=id).first()

    @classmethod
    def create(cls, **kwargs):
        instance = cls.model(**kwargs)
        instance.save()
        return instance

    @classmethod
    def update(cls, id, **kwargs):
        return cls.model.objects(id=id).update(**kwargs)

    @classmethod
    def delete(cls, id):
        return cls.model.objects(id=id).delete()
