from mongoengine import Document, StringField
class Dataset(Document):
    main_prompt = StringField(required=True)
    clip_l = StringField(required=True)
    t5xxl = StringField(required=True)

    meta = {'collection': 'datasets'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "main_prompt": self.main_prompt,
            "clip_l": self.clip_l,
            "t5xxl": self.t5xxl,
        }