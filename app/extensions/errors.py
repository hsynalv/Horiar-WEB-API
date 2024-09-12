import logging
from flask import jsonify
from app.errors.unauthorized_error import UnauthorizedError
from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError

def register_error_handlers(app):
    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(e):
        # UnauthorizedError için loglama (WARNING seviyesi)
        logging.warning(f"Unauthorized access attempt: {e.message}")
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(e):
        # NotFoundError için loglama (WARNING seviyesi)
        logging.warning(f"Resource not found: {e.message}")
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        # ValidationError için loglama (ERROR seviyesi)
        logging.error(f"Validation error: {e.message}")
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(Exception)
    def handle_global_exception(e):
        # Genel hatalar için loglama (ERROR seviyesi)
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        logging.critical(f"Unhandled exception occurred: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": code
        }), code
