from flask import Blueprint, jsonify, url_for, current_app
from ..auth import oauth, create_jwt_token, jwt_required
from app.services.user import UserService

user_bp = Blueprint('user', __name__)

@user_bp.route('/login/discord')
def login_discord():
    discord = oauth.create_client('discord')
    redirect_uri = url_for('user.discord_callback', _external=True)
    return discord.authorize_redirect(redirect_uri)


@user_bp.route('/login/discord/callback')
def discord_callback():
    discord = oauth.create_client('discord')
    token = discord.authorize_access_token()

    # Discord API'sine doğru URL ile istek yapıyoruz
    user_info = discord.get('https://discord.com/api/users/@me').json()

    # Kullanıcı bilgilerini işleme ve veritabanına kaydetme
    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"],
        "email": user_info.get("email"),
        "google_id": None,
        "google_username": None,
    }
    user_id = UserService.add_or_update_user(user_data)

    # JWT oluşturma
    jwt_token = create_jwt_token(user_id, user_info["username"], current_app.config['SECRET_KEY'])

    # JWT'yi JSON yanıtı olarak döndürme
    return jsonify({"token": jwt_token})

@user_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    redirect_uri = url_for('user.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@user_bp.route('/login/google/callback')
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
    print(user_id)

    # JWT oluşturma
    jwt_token = create_jwt_token(user_id, user_info["name"], current_app.config['SECRET_KEY'])

    return jsonify({"token": jwt_token})


# Discord Callback
@user_bp.route('/connect/discord/callback')
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


#@main_bp.route('/getuser', methods=['GET'])
#TODO @jwt_reuqired
@user_bp.route('/getuser/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    #user_id = payload['user_id']
    user = UserService.get_user_by_id(user_id)

    if user:
        return jsonify({
            "user_id": str(user["_id"]),
            "google_id": user.get("google_id"),
            "discord_id": user.get("discord_id"),
            "username": user.get("username"),
            "discord_username": user.get("discord_username"),
            "email": user.get("email")
        })
    else:
        return jsonify({"message": "User not found"}), 404
