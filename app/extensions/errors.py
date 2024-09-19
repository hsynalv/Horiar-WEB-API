import logging
import traceback
from flask import jsonify, request
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

        # Hatanın türüne göre farklı loglama seviyeleri kullanma
        if isinstance(e, ValueError) and "Kullanıcının şifresi yok" in str(e):
            # Şifreyle ilgili hataları WARNING olarak logla
            logging.warning(f"Handled exception: {str(e)}\n"
                            f"URL: {request.url}\n"
                            f"Method: {request.method}\n"
                            f"IP: {request.remote_addr}\n"
                            f"Traceback: {error_trace}")
        else:
            # Diğer tüm hataları CRITICAL olarak logla
            logging.critical(f"Unhandled exception occurred: {str(e)}\n"
                             f"URL: {request.url}\n"
                             f"Method: {request.method}\n"
                             f"IP: {request.remote_addr}\n"
                             f"Traceback: {error_trace}")

        # Hata cevabı döndürme
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": code
        }), code
