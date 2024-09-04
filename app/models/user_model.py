class User:
    def __init__(self, email, username, password=None, google_id=None, google_username=None, discord_id=None,
                 discord_username=None, _id=None):
        self._id = _id
        self.email = email
        self.username = username
        self.password = password
        self.google_id = google_id
        self.google_username = google_username
        self.discord_id = discord_id
        self.discord_username = discord_username

    def to_dict(self):
        user_dict = {
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "google_id": self.google_id,
            "google_username": self.google_username,
            "discord_id": self.discord_id,
            "discord_username": self.discord_username
        }

        if self._id:
            user_dict["_id"] = str(self._id)

        return user_dict

    @staticmethod
    def from_dict(data):
        return User(
            email=data.get("email"),
            username=data.get("username"),
            password=data.get("password"),
            google_id=data.get("google_id"),
            google_username=data.get("google_username"),
            discord_id=data.get("discord_id"),
            discord_username=data.get("discord_username"),
            _id=data.get("_id")
        )
