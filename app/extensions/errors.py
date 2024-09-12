from flask import jsonify
from app.errors.unauthorized_error import UnauthorizedError
from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError

def register_error_handlers(app):
    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(Exception)
    def handle_global_exception(e):
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": code
        }), code
