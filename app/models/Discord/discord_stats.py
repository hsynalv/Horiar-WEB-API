from mongoengine import Document, IntField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField, FloatField
from datetime import datetime

class UsageStats(EmbeddedDocument):
    total_image_generated = IntField(db_field='totalImageGenerated', required=True)
    total_variations_created = IntField(db_field='totalVariationsCreated', required=True)
    success_rate = FloatField(db_field='successRate', required=True)

class GeneralStats(EmbeddedDocument):
    total_servers = IntField(db_field='totalServers', required=True)
    unique_users = IntField(db_field='uniqueUsers', required=True)

class DiscordStats(Document):
    usage_stats = EmbeddedDocumentField(UsageStats, db_field='usageStats', required=True)
    general_stats = EmbeddedDocumentField(GeneralStats, db_field='generalStats', required=True)
    last_updated = DateTimeField(db_field='lastUpdated', required=True)
    created_at = DateTimeField(db_field='createdAt', required=True)
    updated_at = DateTimeField(db_field='updatedAt', required=True)
    __v = IntField(db_field='__v', default=0)

    meta = {
        'db_alias': "secondary",
        'collection': 'statistics'
    }

    def to_dict(self):
        return {
            "__v": self.__v,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "generalStats": self.general_stats.to_mongo() if self.general_stats else None,
            "lastUpdated": self.last_updated.isoformat() if self.last_updated else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "usageStats": self.usage_stats.to_mongo() if self.usage_stats else None
        }
