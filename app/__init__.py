import os
from flask import Flask
from flask_cors import CORS
from flask_wtf import CSRFProtect
from mongoengine import connect
from dotenv import load_dotenv

from .auth import configure_oauth
from .routes.text_to_image_routes import text_to_image_bp

# Extensions ve helper fonksiyonları içe aktar
from app.extensions.errors import register_error_handlers
from app.extensions.blueprints import register_blueprints

# Ortam değişkenine göre doğru .env dosyasını yükle
env_file = ".env.development" if os.getenv('FLASK_ENV') == 'development' else ".env.production"
load_dotenv(env_file)  # Doğru .env dosyasını yükle

# Ortam yapılandırma dosyalarını içe aktar
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig
from app.extensions.logging_config import setup_logging
from app.auth import configure_oauth

def create_app():

    app = Flask(__name__)

    # Loglama yapılandırmasını başlat
    setup_logging()

    csrf = CSRFProtect()
    csrf.init_app(app)

    # Ortam değişkenine göre yapılandırmayı yükle
    if os.getenv('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # CORS ayarları (Üretim ve Geliştirme için farklı olabilir)
    if app.config.get('ENV', 'development') == 'production':
        CORS(app, resources={r"/api/*": {"origins": "https://your-production-site.com"}})
    else:
        CORS(app, supports_credentials=True)

    # MongoEngine bağlantısı
    connect(host=app.config["MONGO_URI"])

    # OAuth'u başlat
    configure_oauth(app)

    # Blueprint'leri kaydetme
    register_blueprints(app)

    # Global hata yönetimi
    register_error_handlers(app)

    return app
