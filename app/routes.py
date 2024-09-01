from flask import Blueprint, url_for, current_app, jsonify
from .auth import oauth, create_jwt_token, jwt_required
from .user import UserService


main_bp = Blueprint('main', __name__)

@main_bp.route('/status', methods=['GET'])
def status():
    return {"status": "API is running"}

@main_bp.route('/login/discord')
def login_discord():
    discord = oauth.create_client('discord')
    redirect_uri = url_for('main.discord_callback', _external=True)
    return discord.authorize_redirect(redirect_uri)


@main_bp.route('/login/discord/callback')
def discord_callback():
    discord = oauth.create_client('discord')
    token = discord.authorize_access_token()

    # Discord API'sine doğru URL ile istek yapıyoruz
    user_info = discord.get('https://discord.com/api/users/@me').json()

    # Kullanıcı bilgilerini işleme ve veritabanına kaydetme
    user_data = {
        "discord_id": user_info["id"],
        "username": user_info["username"],
        "email": user_info.get("email")
    }
    user_id = UserService.add_or_update_user(user_data)

    # JWT oluşturma
    jwt_token = create_jwt_token(user_info["id"], user_info["username"], current_app.config['SECRET_KEY'])

    # JWT'yi JSON yanıtı olarak döndürme
    return jsonify({"token": jwt_token})

@main_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    redirect_uri = url_for('main.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@main_bp.route('/login/google/callback')
def google_callback():
    google = oauth.create_client('google')
    token = google.authorize_access_token()

    # Google API'sinden kullanıcı bilgilerini alma
    user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    # Kullanıcı bilgilerini veritabanına geçici olarak kaydetme
    user_data = {
        "google_id": user_info["id"],
        "username": user_info["name"],
        "email": user_info["email"],
        "discord_id": None,
        "discord_username": None
    }
    user_id = UserService.add_or_update_user(user_data)

    # JWT oluşturma
    jwt_token = create_jwt_token(user_id, user_info["name"], current_app.config['SECRET_KEY'])

    return jsonify({"message": "Google ile kayıt oldunuz. Lütfen Discord ile bağlantı kurarak işlemi tamamlayın.", "token": jwt_token})

# Discord Callback
@main_bp.route('/connect/discord/callback')
@jwt_required
def connect_discord_callback(payload):
    discord = oauth.create_client('discord')
    token = discord.authorize_access_token()

    # Discord API'sinden kullanıcı bilgilerini alma
    user_info = discord.get('https://discord.com/api/users/@me').json()

    # Kullanıcı profilini Discord bilgileriyle güncelleme
    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"]
    }
    UserService.update_user_by_google_id(payload['user_id'], user_data)

    return jsonify({"message": "Discord ile bağlantı başarılı.", "discord_id": user_info["id"], "discord_username": user_info["username"]})