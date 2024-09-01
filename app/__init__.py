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

    # Blueprint'leri buraya ekleyebilirsiniz
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
