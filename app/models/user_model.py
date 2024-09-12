from mongoengine import Document, StringField, EmailField

class User(Document):
    email = EmailField(required=True, unique=True)
    username = StringField(required=True, max_length=50)
    password = StringField()
    google_id = StringField()
    google_username = StringField()
    discord_id = StringField()
    discord_username = StringField()

    meta = {'collection': 'users'}

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "google_id": self.google_id,
            "google_username": self.google_username,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username
        }
