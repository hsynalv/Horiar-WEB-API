import logging
import os
from flask import Flask, request
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_mongoengine import MongoEngine
from dotenv import load_dotenv
from flask_socketio import SocketIO

from app.auth import configure_oauth
from app.extensions.socketio import socketio
from app.models.user_model import User
from app.routes.text_to_image_routes import text_to_image_bp

# Extensions ve helper fonksiyonları içe aktar
from app.extensions.errors import register_error_handlers
from app.extensions.blueprints import register_blueprints
from app.extensions.logging_config import setup_logging
from app.extensions.admin import configure_admin
from app.extensions.mail import mail

# Ortam değişkenine göre doğru .env dosyasını yükle
env_file = ".env.development" if os.getenv('FLASK_ENV') == 'development' else ".env.production"
load_dotenv(env_file)  # Doğru .env dosyasını yükle

# Ortam yapılandırma dosyalarını içe aktar
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig

# MongoEngine örneği oluştur
db = MongoEngine()

# LoginManager oluştur
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)


    # Loglama yapılandırmasını başlat
    setup_logging()

    # Yeni: SocketIO uygulamaya entegre edildi
    socketio.init_app(app)

    # Ortam değişkenine göre yapılandırmayı yükle
    if app.config['ENV'] == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    print(app.config['ENV'])
    logging.info(app.config['ENV'])

    if app.config['ENV'] == 'production':
        CORS(app, resources={
            r"/*": {"origins": ["https://www.horiar.com", "https://horiar.com", "http://localhost:5000",
                                "http://127.0.0.1:5500", "http://127.0.0.1:3000"], "supports_credentials": True}})
    else:
        CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    # MongoDB bağlantı ayarları .env'den çekiliyor
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        raise ValueError("MONGO_URI not set in the environment variables.")

    app.config['MONGODB_SETTINGS'] = {
        'host': mongo_uri
    }

    # MongoDB bağlantısını başlat
    db.init_app(app)

    # Ortam değişkenlerinden ayarları yükle
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    app.config['MAIL_DEBUG'] = int(os.getenv('MAIL_DEBUG', 0))

    # Flask-Mail başlat
    mail.init_app(app)

    # Flask-Admin'i yapılandır
    configure_admin(app)

    # OAuth'u başlat
    configure_oauth(app)

    # Blueprint'leri kaydetme
    register_blueprints(app)

    # Global hata yönetimi
    register_error_handlers(app)

    # LoginManager yapılandırması
    login_manager.init_app(app)  # Uygulamaya login_manager'i ekliyoruz
    login_manager.login_view = 'admin_auth_bp.login'  # Oturum açılmadığında yönlendirilecek sayfa

    # Kullanıcıyı yüklemek için gerekli user_loader fonksiyonu
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()

    return app
