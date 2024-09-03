from flask import current_app, jsonify, request
from authlib.integrations.flask_client import OAuth
import jwt
import datetime


oauth = OAuth()

def configure_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='discord',
        client_id=app.config['DISCORD_CLIENT_ID'],
        client_secret=app.config['DISCORD_CLIENT_SECRET'],
        authorize_url='https://discord.com/api/oauth2/authorize',
        access_token_url='https://discord.com/api/oauth2/token',
        redirect_uri='http://127.0.0.1:5000/login/discord/callback',# TODO: Geri Dönüşü burada ve discord dev de düzeltmek gerek
        client_kwargs={'scope': 'identify email'}
    )

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        redirect_uri=app.config['GOOGLE_REDIRECT_URI'],
        client_kwargs={'scope': 'openid email profile'}
    )


def create_jwt_token(user_id, username, secret_key):

    payload = {
        "user_id": str(user_id),  # _id ObjectId türünde olduğu için stringe çeviriyoruz
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)  # Token geçerlilik süresi
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def verify_jwt_token(token, secret_key):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token süresi dolmuş
    except jwt.InvalidTokenError:
        return None  # Geçersiz token

def jwt_required(f):
    """
    JWT doğrulaması yapan middleware.
    """
    def jwt_wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1]
        else:
            return jsonify({"message": "Token is missing!"}), 403

        payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])
        if payload is None:
            return jsonify({"message": "Token is invalid or expired!"}), 403

        return f(payload, *args, **kwargs)
    return jwt_wrapper
