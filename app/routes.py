from flask import Blueprint, url_for, redirect
from .auth import oauth
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
    user_info = discord.get('https://discord.com/api/users/@me').json()

    # Kullanıcı bilgilerini MongoDB'ye kaydetme veya güncelleme
    user_data = {
        "discord_id": user_info["id"],
        "username": user_info["username"],
        "email": user_info.get("email")
    }
    UserService.add_or_update_user(user_data)

    return redirect(url_for('main.status')) #TODO: Yönlendir işlemini burada kontrol et
