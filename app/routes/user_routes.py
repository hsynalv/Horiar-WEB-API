from flask import Blueprint, jsonify, request, current_app, make_response, redirect, url_for
from ..auth import create_jwt_token, jwt_required, oauth
from app.services.user import UserService
import jwt

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

    user_info = discord.get('https://discord.com/api/users/@me').json()

    user_data = {
        "discord_id": user_info["id"],
        "discord_username": user_info["username"],
        "email": user_info.get("email"),
        "google_id": None,
        "google_username": None,
        "password": None
    }

    user_id = UserService.add_or_update_user(user_data)

    jwt_token = create_jwt_token(str(user_id), user_info["username"], user_info["email"],current_app.config['SECRET_KEY'])

    response = make_response(redirect("http://127.0.0.1:3000"))
    response.set_cookie('token', jwt_token, httponly=False, secure=False, samesite='Lax')
    response.set_cookie('userId', str(user_id), httponly=False, secure=False, samesite='Lax')

    return response

@user_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    redirect_uri = url_for('user.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@user_bp.route('/login/google/callback')
def google_callback():
    google = oauth.create_client('google')
    token = google.authorize_access_token()

    user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    user_data = {
        "google_id": user_info["id"],
        "username": user_info["name"],
        "email": user_info["email"],
        "discord_id": None,
        "discord_username": None,
        "password": None
    }
    user_id = UserService.add_or_update_user(user_data)

    jwt_token = create_jwt_token(str(user_id), user_info["name"], user_info["email"],current_app.config['SECRET_KEY'])

    response = make_response(redirect("http://127.0.0.1:3000"))
    response.set_cookie('token', jwt_token, httponly=False, secure=False, samesite='Lax')
    response.set_cookie('userId', str(user_id), httponly=False, secure=False, samesite='Lax')

    return response

@user_bp.route('/getuser/<user_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_user_by_id(user_id):
    user = UserService.get_user_by_id(user_id)

    if user:
        return jsonify(user), 200
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
    token = create_jwt_token(str(user._id), user.username, user.email, current_app.config['SECRET_KEY'])

    response_data = {
        "message": "Login successful",
        "token": token,
        "userId": str(user._id),
        "username": user.username,
        "email": user.email,
    }
    return jsonify(response_data), 200
