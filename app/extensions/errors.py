import logging
import traceback
from flask import jsonify, request, current_app
from app.errors.unauthorized_error import UnauthorizedError
from app.errors.not_found_error import NotFoundError
from app.errors.validation_error import ValidationError
from app.utils.mail_utils import send_error_email


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

    @app.errorhandler(404)
    def not_found_error(e):
        # Loglama işlemi
        logging.warning(
            f"404 Not Found: Requested URL: {request.url}, "
            f"Method: {request.method}, "
            f"IP: {get_client_ip()}"
        )
        send_error_email(subject="Critical Error in Application", error_details="deneme hata live")
        # İsteğe bağlı olarak kullanıcıya 404 yanıtı döndürme
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(Exception)
    def handle_global_exception(e):
        # Hata kodu belirleme
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        # Hata yığın izini almak
        error_trace = traceback.format_exc()
        client_ip = get_client_ip()
        # Hatanın türüne göre farklı loglama seviyeleri kullanma
        if isinstance(e, ValueError) and "Kullanıcının şifresi yok" in str(e):
            # Şifreyle ilgili hataları WARNING olarak logla
            logging.warning(f"Handled exception: {str(e)}\n"
                            f"URL: {request.url}\n"
                            f"Method: {request.method}\n"
                            f"IP: {client_ip}\n"
                            f"Traceback: {error_trace}")
        else:
            # Diğer tüm hataları CRITICAL olarak logla ve e-posta gönder
            logging.critical(f"Unhandled exception occurred: {str(e)}\n"
                             f"URL: {request.url}\n"
                             f"Method: {request.method}\n"
                             f"IP: {client_ip}\n"
                             f"Traceback: {error_trace}")
        error_details = f"Unhandled exception occurred: {str(e)}\n" \
                        f"URL: {request.url}\n" \
                        f"Method: {request.method}\n" \
                        f"IP: {client_ip}\n" \
                        f"Traceback: {error_trace}"
        send_error_email(subject="Critical Error in Application", error_details=error_details)
        # Hata cevabı döndürme
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": code
        }), code

    # Gerçek istemci IP adresini almak için fonksiyon
    def get_client_ip():
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip_address = request.remote_addr
        return ip_address
