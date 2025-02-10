from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField, ListField, FloatField
from datetime import datetime

class UsageStats(EmbeddedDocument):
    total_image_generated = IntField(db_field='totalImageGenerated', required=True)
    total_variations_created = IntField(db_field='totalVariationsCreated', required=True)
    success_rate = FloatField(db_field='successRate', required=True)

class Server(EmbeddedDocument):
    _id = StringField()
    server_id = StringField(db_field='serverId', required=True)
    server_name = StringField(db_field='serverName', required=True)
    member_count = IntField(db_field='memberCount', required=True)
    join_date = DateTimeField(db_field='joinDate', required=True)
    last_active = DateTimeField(db_field='lastActive', required=True)
    total_requests = IntField(db_field='totalRequests', required=True)
    is_active = BooleanField(db_field='isActive', required=True)

class DailyStat(EmbeddedDocument):
    _id = StringField()
    date = DateTimeField(required=True)
    total_requests = IntField(db_field='totalRequests' ,required=True)
    unique_users = IntField(db_field='uniqueUsers', required=True)
    successful_requests = IntField(db_field='successfulRequests' ,required=True)
    failed_requests = IntField(db_field='failedRequests', required=True)

class DiscordStats(Document):
    usage_stats = EmbeddedDocumentField(UsageStats, db_field='usageStats', required=True)
    total_users = IntField(db_field='totalUsers' ,required=True)
    total_servers = IntField(db_field='totalServers', required=True)
    total_requests = IntField(db_field='totalRequests',required=True)
    servers = ListField(EmbeddedDocumentField(Server))
    daily_stats = ListField(EmbeddedDocumentField(DailyStat), db_field='dailyStats')
    last_updated = DateTimeField(db_field='lastUpdated' ,default=datetime.utcnow)
    created_at = DateTimeField(db_field='createdAt',default=datetime.utcnow)
    updated_at = DateTimeField(db_field='updatedAt', default=datetime.utcnow)
    __v = IntField(db_field='__v')

    meta = {
        'db_alias': "secondary",
        'collection': 'statistics'
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "usage_stats": self.usage_stats.to_mongo(),
            "total_users": self.total_users,
            "total_servers": self.total_servers,
            "total_requests": self.total_requests,
            "servers": [server.to_mongo() for server in self.servers],
            "daily_stats": [stat.to_mongo() for stat in self.daily_stats],
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
