class NotFoundError(Exception):
    status_code = 404

    def __init__(self, message="Resource not found"):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return {
            "error": "Not Found",
            "message": self.message,
            "code": self.status_code

        }
