class ValidationError(Exception):
    status_code = 400

    def __init__(self, message="Invalid data provided"):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return {
            "error": "Bad Request",
            "message": self.message,
            "code": self.status_code
        }
