from mongoengine import Document, StringField, IntField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, FloatField, BooleanField
from datetime import datetime

class OriginalImage(EmbeddedDocument):
    url = StringField(db_field='url', required=True)
    seed = IntField(db_field='seed', required=True)
    guidance = FloatField(db_field='guidance', required=True)
    _id = StringField(db_field='_id')

class Request(EmbeddedDocument):
    type = StringField(db_field='type', required=True)
    messageId = StringField(db_field='messageId', required=True)
    timestamp = DateTimeField(db_field='timestamp', required=True)
    status = StringField(db_field='status', required=True)
    prompt = StringField(db_field='prompt', required=True)
    resolution = StringField(db_field='resolution', required=True)
    modelType = StringField(db_field='modelType', required=True)
    originalImages = ListField(EmbeddedDocumentField(OriginalImage), db_field='originalImages')
    _id = StringField(db_field='_id')

    @property
    def as_dict(self):
        return {
            "type": self.type,
            "messageId": self.messageId,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "status": self.status,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "modelType": self.modelType,
            "_id": str(self._id) if self._id else None,
            "originalImages": [{"url": oi.url, "seed": oi.seed} for oi in self.originalImages]
        }

class Statistics(EmbeddedDocument):
    failureCount = IntField(db_field='failureCount', required=True)
    generateCount = IntField(db_field='generateCount', required=True)
    recreateCount = IntField(db_field='recreateCount', required=True)
    successCount = IntField(db_field='successCount', required=True)
    upscaleCount = IntField(db_field='upscaleCount', required=True)

class DiscordUsers(Document):
    _id = StringField(db_field='_id', required=True)
    userId = StringField(db_field='userId', required=True)
    createdAt = DateTimeField(db_field='createdAt', required=True)
    firstSeen = DateTimeField(db_field='firstSeen', required=True)
    lastSeen = DateTimeField(db_field='lastSeen', required=True)
    requests = ListField(EmbeddedDocumentField(Request), db_field='requests')
    statistics = EmbeddedDocumentField(Statistics, db_field='statistics', required=True)
    totalRequests = IntField(db_field='totalRequests', required=True)
    updatedAt = DateTimeField(db_field='updatedAt', required=True)
    username = StringField(db_field='username', required=True)

    meta = {
        'db_alias': 'secondary',  # Veritabanı bağlantı adı
        'collection': 'users'     # MongoDB koleksiyon adı
    }

    @property
    def requests_json(self):
        # Her bir Request için as_dict property'sini kullanıp liste döndürür
        return [req.as_dict for req in self.requests]

    def to_dict(self):
        return {
            "id": str(self.id),
            "userId": self.userId,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "firstSeen": self.firstSeen.isoformat() if self.firstSeen else None,
            "lastSeen": self.lastSeen.isoformat() if self.lastSeen else None,
            "requests": [req.to_dict() for req in self.requests],  # Bu alan template'te kullanılmayacak
            "statistics": self.statistics.to_mongo(),
            "totalRequests": self.totalRequests,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
            "username": self.username
        }