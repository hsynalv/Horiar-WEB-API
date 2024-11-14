import logging
import datetime
import time

from flask import Blueprint, jsonify, request, current_app, make_response, redirect, url_for
from ..auth import create_jwt_token, jwt_required, oauth
from app.services.user_service import UserService
from ..services.subscription_service import SubscriptionService

user_bp = Blueprint('user_bp', __name__)
MAX_RETRIES = 3  # Yeniden deneme sayısı
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
            return redirect("https://horiar.com")

    user_info = discord.get('https://discord.com/api/users/@me').json()

    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"],
        "username": user_info["username"],
        "email": user_info.get("email"),
        "google_id": None,
        "google_username": None,
        "password": None,
        "is_enabled": True,  # Kullanıcı varsayılan olarak aktif olabilir
        "is_banned": False,  # Varsayılan olarak yasaklanmamış olabilir
        "roles": ["37fb8744-faf9-4f62-a729-a284c842bf0a"],  # Discord üzerinden gelenler 'user' rolüyle atanabilir
        "base_credits": 15
    }

    # Kullanıcıyı ekler veya günceller ve kullanıcı nesnesini alır
    user = UserService.add_or_update_user(user_data)

    # JWT oluşturmak için kullanıcı bilgilerini kullan
    jwt_token = create_jwt_token(str(user.id), user.username, user.email, user.roles, current_app.config['SECRET_KEY'])

    response = make_response(redirect("https://horiar.com"))
    response.set_cookie('token', jwt_token, httponly=False, secure=True, samesite='None', domain='.horiar.com', max_age=30*24*60*60)
    response.set_cookie('userId', str(user.id), httponly=False, secure=True, samesite='None', domain='.horiar.com', max_age=30*24*60*60)
    response.set_cookie('sn', user.roles[0], httponly=False, secure=True, samesite='None', domain='.horiar.com', max_age=30*24*60*60)
    response.set_cookie('logtype', "oauth-432bc057179a", httponly=False, secure=True, samesite='None', domain='.horiar.com', max_age=30*24*60*60)

    return response


@user_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    redirect_uri = url_for('user_bp.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri, prompt='select_account')


@user_bp.route('/login/google/callback')
def google_callback():
    google = oauth.create_client('google')

    # Yeniden deneme için döngü
    for attempt in range(MAX_RETRIES):
        try:
            # Google'dan yetkilendirme token'ını almayı deneyin
            token = google.authorize_access_token(timeout=30)
            break  # Eğer başarıyla token alınırsa döngüyü kır
        except Exception as e:
            error_message = str(e)
            logging.error(f"Google login sırasında hata meydana geldi: {error_message}")

            if "access_denied" in error_message:
                return redirect("https://horiar.com/explore")  # İptal durumunda yönlendirme

            if "Read timed out" in error_message and attempt < MAX_RETRIES - 1:
                time.sleep(2)  # 2 saniye bekle ve yeniden dene
                continue  # Yeniden denemeye devam et

            # Hata devam ederse kullanıcıyı bilgilendirmeden ana sayfaya yönlendirin
            return redirect("https://horiar.com")

    try:
        # Kullanıcı bilgilerini Google API'den alıyoruz
        user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo', timeout=10).json()
    except Exception as e:
        logging.error(f"Kullanıcı bilgilerini alırken hata: {str(e)}")
        return redirect("https://horiar.com")

    # Kullanıcı verilerini hazırlama
    user_data = {
        "google_id": user_info["id"],
        "username": user_info["name"],
        "email": user_info["email"],
        "discord_id": None,
        "discord_username": None,
        "google_username": user_info["name"],
        "password": None,
        "is_enabled": True,
        "is_banned": False,
        "roles": ["37fb8744-faf9-4f62-a729-a284c842bf0a"],
        "base_credits": 15
    }

    # Kullanıcıyı ekler veya günceller ve kullanıcı nesnesini alır
    user = UserService.add_or_update_user(user_data)

    # JWT oluşturmak için kullanıcı bilgilerini kullan
    jwt_token = create_jwt_token(
        str(user.id), user.username, user.email, user.roles,
        current_app.config['SECRET_KEY']
    )

    # Kullanıcıya cookie göndererek yanıt oluşturma
    response = make_response(redirect("https://horiar.com"))
    response.set_cookie('token', jwt_token, httponly=False, secure=True, samesite='None', domain='.horiar.com',
                        max_age=30 * 24 * 60 * 60)
    response.set_cookie('userId', str(user.id), httponly=False, secure=True, samesite='None', domain='.horiar.com',
                        max_age=30 * 24 * 60 * 60)
    response.set_cookie('sn', user.roles[0], httponly=False, secure=True, samesite='None', domain='.horiar.com',
                        max_age=30 * 24 * 60 * 60)
    response.set_cookie('logtype', "oauth-432bc057179a", httponly=False, secure=True, samesite='None',
                        domain='.horiar.com', max_age=30 * 24 * 60 * 60)

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

    try:
        user_id = UserService.add_user(email, password)
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

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Şifre olup olmadığını kontrol edin
    if user.password is None:
        return jsonify({"message": "This user doesn't have a password. Please use Google or Discord login."}), 400

    if not UserService.check_password(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    user.last_login_date = datetime.datetime.utcnow()
    user.save()

    # Generate JWT token with email and user information
    token = create_jwt_token(str(user.id), user.username, user.email, user.roles, current_app.config['SECRET_KEY'])
    subscription = SubscriptionService.get_subscription_by_id(str(user.id))
    if subscription is None:
        credits = user.base_credits
    else:
        credits = subscription.credit_balance

    response_data = {
        "message": "Login successful",
        "token": token,
        "userId": str(user.id),
        "username": user.username,
        "email": user.email,
        "credits": credits
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

    return redirect("https://horiar.com")

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

@user_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({"message": "Logout successful"})
    response.delete_cookie('token', domain='.horiar.com')
    response.delete_cookie('userId', domain='.horiar.com')
    response.delete_cookie('sn', domain='.horiar.com')
    response.delete_cookie('logtype', domain='.horiar.com')
    return response

@user_bp.route('/change-password', methods=['POST'])
@jwt_required(pass_payload=True)
def change_password(payload):
    data = request.json
    try:
        UserService.change_password(payload['sub'], data.get('current_password'), data.get('new_password'))
        return jsonify({"message": "Password changed successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@user_bp.route('/update_user_status', methods=['POST'])
#@jwt_required(pass_payload=False)
def update_user_status():
    data = request.get_json()
    user_id = data.get('user_id')
    field = data.get('field')
    value = data.get('value')

    if not user_id or not field:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        update_data = {field: value}
        UserService.update_user_by_id(user_id, update_data)
        return jsonify({"message": "User status updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/get-user-credit', methods=['GET'])
@jwt_required(pass_payload=True)
def get_user_credit(payload):
    user_id = payload['sub']
    credit = UserService.get_user_credit(user_id)
    return credit


@user_bp.route('/get-all-requests', methods=['GET'])
@jwt_required(pass_payload=True)
def get_user_requests(payload):
    # URL'den sayfa ve sayfa boyutu bilgilerini alıyoruz, varsayılan olarak page=1 ve page_size=10
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)

    # Kullanıcının renderlarını alıyoruz
    renders = UserService.get_all_requests(payload, page=page, page_size=page_size)

    return jsonify(renders)
