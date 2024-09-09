from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from .config import Config
from .auth import configure_oauth
from .routes.text_to_image_routes import text_to_image_bp
def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_object(Config)

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
