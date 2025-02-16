from mongoengine import Document, StringField, IntField, DateTimeField
from datetime import datetime

class DiscordServer(Document):
    _id = StringField(db_field='_id', required=True)
    serverId = StringField(db_field='serverId', required=True)
    __v = IntField(db_field='__v', default=0)
    joinDate = DateTimeField(db_field='joinDate', required=True)
    lastRequest = DateTimeField(db_field='lastRequest', required=True)
    memberCount = IntField(db_field='memberCount', required=True)
    serverName = StringField(db_field='serverName', required=True)
    totalRequests = IntField(db_field='totalRequests', required=True)

    meta = {
        'db_alias': 'secondary',
        'collection': 'servers'
    }

    def to_dict(self):
        return {
            "_id": str(self._id),
            "serverId": self.serverId,
            "__v": self.__v,
            "joinDate": self.joinDate.isoformat() if self.joinDate else None,
            "lastRequest": self.lastRequest.isoformat() if self.lastRequest else None,
            "memberCount": self.memberCount,
            "serverName": self.serverName,
            "totalRequests": self.totalRequests
        }
