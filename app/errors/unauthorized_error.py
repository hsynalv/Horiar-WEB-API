class UnauthorizedError(Exception):
    status_code = 401

    def __init__(self, message="Unauthorized access"):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return {
            "error": "Unauthorized",
            "message": self.message,
            "code": self.status_code
        }
