from flask import Flask
from .config import Config
from pymongo import MongoClient
from .auth import configure_oauth

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # MongoDB bağlantısı
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client.get_database()

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

    return app
