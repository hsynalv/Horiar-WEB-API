import logging
import traceback
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
        # Hata kodu belirleme
        code = 500
        if hasattr(e, 'code'):
            code = e.code

        # Hata yığın izini almak
        error_trace = traceback.format_exc()

        # Hatanın nerede oluştuğunu ve yığın izini loglama (CRITICAL seviyesi)
        logging.critical(f"Unhandled exception occurred: {str(e)}\nTraceback: {error_trace}")

        # Hata cevabı döndürme
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": code
        }), code
