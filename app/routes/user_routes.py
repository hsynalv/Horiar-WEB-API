import logging

from flask import Blueprint, jsonify, request, current_app, make_response, redirect, url_for
from ..auth import create_jwt_token, jwt_required, oauth
from app.services.user_service import UserService


user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/login/discord')
def login_discord():
    discord = oauth.create_client('discord')
    redirect_uri = url_for('user_bp.discord_callback', _external=True)
    return discord.authorize_redirect(redirect_uri)

@user_bp.route('/login/discord/callback')
def discord_callback():
    discord = oauth.create_client('discord')

    try:
        # Discord'dan yetkilendirme token'ını almayı deneyin
        token = discord.authorize_access_token()
    except Exception as e:
        # Eğer "access_denied" hatası gelirse kullanıcıyı istediğiniz yere yönlendirin
        error_message = str(e)
        if "access_denied" in error_message:
            return redirect("https://horiar.com/explore")  # İptal durumunda yönlendirme
        else:
            logging.error(f"Discord login sırasında hata meydana geldi: {error_message}")
            return redirect("https://horiar.com/explore")

    user_info = discord.get('https://discord.com/api/users/@me').json()

    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"],
        "username": user_info["username"],
        "email": user_info.get("email"),
        "google_id": None,
        "google_username": None,
        "password": None,
        "is_active": True,  # Kullanıcı varsayılan olarak aktif olabilir
        "is_banned": False,  # Varsayılan olarak yasaklanmamış olabilir
        "roles": ["37fb8744-faf9-4f62-a729-a284c842bf0a"]  # Discord üzerinden gelenler 'user' rolüyle atanabilir
    }

    user_id = UserService.add_or_update_user(user_data)

    jwt_token = create_jwt_token(str(user_id), user_info["username"], user_info["email"], user_data["roles"], current_app.config['SECRET_KEY'])

    response = make_response(redirect("https://horiar.com/explore"))
    response.set_cookie('token', jwt_token, httponly=False, secure=True, samesite='None', domain='.horiar.com')
    response.set_cookie('userId', str(user_id), httponly=False, secure=True, samesite='None', domain='.horiar.com')

    return response

@user_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    redirect_uri = url_for('user_bp.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@user_bp.route('/login/google/callback')
def google_callback():
    google = oauth.create_client('google')
    try:
        # Discord'dan yetkilendirme token'ını almayı deneyin
        token = google.authorize_access_token()
    except Exception as e:
        # Eğer "access_denied" hatası gelirse kullanıcıyı istediğiniz yere yönlendirin
        error_message = str(e)
        if "access_denied" in error_message:
            return redirect("https://horiar.com/explore")  # İptal durumunda yönlendirme
        else:
            logging.error(f"Discord login sırasında hata meydana geldi: {error_message}")
            return redirect("https://horiar.com/explore")

    user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    user_data = {
        "google_id": user_info["id"],
        "username": user_info["name"],
        "email": user_info["email"],
        "discord_id": None,
        "discord_username": None,
        "password": None,
        "is_active": True,  # Kullanıcı varsayılan olarak aktif olabilir
        "is_banned": False,  # Varsayılan olarak yasaklanmamış olabilir
        "roles": ["37fb8744-faf9-4f62-a729-a284c842bf0a"]  # Discord üzerinden gelenler 'user' rolüyle atanabilir
    }
    user_id = UserService.add_or_update_user(user_data)

    jwt_token = create_jwt_token(str(user_id), user_info["name"], user_info["email"],user_data["roles"], current_app.config['SECRET_KEY'])

    response = make_response(redirect("https://horiar.com/explore"))
    response.set_cookie('token', jwt_token, httponly=False, secure=True, samesite='None', domain='.horiar.com')
    response.set_cookie('userId', str(user_id), httponly=False, secure=True, samesite='None', domain='.horiar.com')

    return response

@user_bp.route('/getuser/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_user_by_id(user_id):
    user = UserService.get_user_by_id(user_id)

    if user:
        return jsonify(user.to_dict()), 200
    else:
        return jsonify({"message": "User not found"}), 404

@user_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    try:
        user_id = UserService.add_user(email, password, username)
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    user = UserService.find_user_by_email(email)
    if not user or not UserService.check_password(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate JWT token with email and user information
    token = create_jwt_token(str(user.id), user.username, user.email, user.roles, current_app.config['SECRET_KEY'])

    response_data = {
        "message": "Login successful",
        "token": token,
        "userId": str(user.id),
        "username": user.username,
        "email": user.email,
    }
    return jsonify(response_data), 200

@user_bp.route('/connect/google')
@jwt_required(pass_payload=True)
def connect_google(payload):
    google = oauth.create_client('google')
    redirect_uri = url_for('user_bp.connect_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@user_bp.route('/connect/google/callback')
@jwt_required(pass_payload=True)
def connect_google_callback(payload):
    google = oauth.create_client('google')
    try:
        token = google.authorize_access_token()
    except Exception as e:
        # Eğer "access_denied" hatası gelirse kullanıcıyı istediğiniz yere yönlendirin
        error_message = str(e)
        if "access_denied" in error_message:
            return redirect("https://horiar.com/user")  # İptal durumunda yönlendirme
        else:
            logging.error(f"Discord login sırasında hata meydana geldi: {error_message}")
            return redirect("https://horiar.com/user")

    user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    # Mevcut kullanıcının Google hesabını bağlama
    user_id = payload['sub']  # Mevcut kullanıcının ID'sini JWT'den alıyoruz
    user_data = {
        "google_id": user_info["id"],
        "google_username": user_info["name"],
    }
    UserService.update_user_by_id(user_id, user_data)

    return redirect("https://horiar.com/explore")

@user_bp.route('/connect/discord')
@jwt_required(pass_payload=True)
def connect_discord(payload):
    discord = oauth.create_client('discord')
    redirect_uri = url_for('user_bp.connect_discord_callback', _external=True)
    return discord.authorize_redirect(redirect_uri)

@user_bp.route('/connect/discord/callback')
@jwt_required(pass_payload=True)
def connect_discord_callback(payload):
    discord = oauth.create_client('discord')
    try:
        token = discord.authorize_access_token()
    except Exception as e:
        # Eğer "access_denied" hatası gelirse kullanıcıyı istediğiniz yere yönlendirin
        error_message = str(e)
        if "access_denied" in error_message:
            return redirect("https://horiar.com/user")  # İptal durumunda yönlendirme
        else:
            logging.error(f"Discord login sırasında hata meydana geldi: {error_message}")
            return redirect("https://horiar.com/user")

    user_info = discord.get('https://discord.com/api/users/@me').json()

    # Mevcut kullanıcının Discord hesabını bağlama
    user_id = payload['sub']  # Mevcut kullanıcının ID'sini JWT'den alıyoruz
    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"]
    }
    UserService.update_user_by_id(user_id, user_data)

    return redirect("https://horiar.com/explore")

