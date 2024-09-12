from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
import os
from .auth import configure_oauth
from .routes.text_to_image_routes import text_to_image_bp
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Ortam değişkenine göre doğru .env dosyasını yükle
env_file = ".env.development" if os.getenv('FLASK_ENV') == 'development' else ".env.production"
load_dotenv(env_file)  # Doğru .env dosyasını yükle

# Ortam yapılandırma dosyalarını içe aktar
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig
def create_app():

    app = Flask(__name__)

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

    # MongoDB bağlantısı
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client.get_database("horiar")

    # Varsayılan kullanıcı koleksiyonunu kontrol etme ve oluşturma
    if "users" not in app.db.list_collection_names():
        app.db.create_collection("users")

    # OAuth'u başlat
    configure_oauth(app)

    # Blueprint'leri kaydetme
    from .routes.user_routes import user_bp
    from .routes.package_routes import package_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(package_bp, url_prefix='/package')
    app.register_blueprint(text_to_image_bp, url_prefix='/create')

    return app
