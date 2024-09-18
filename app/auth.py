from flask import current_app, jsonify, request
from authlib.integrations.flask_client import OAuth
import jwt
import datetime
import uuid
from functools import wraps


oauth = OAuth()

def configure_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='discord',
        client_id=app.config['DISCORD_CLIENT_ID'],
        client_secret=app.config['DISCORD_CLIENT_SECRET'],
        authorize_url='https://discord.com/api/oauth2/authorize',
        access_token_url='https://discord.com/api/oauth2/token',
        redirect_uri=app.config['DISCORD_REDIRECT_URI'],# TODO: Geri Dönüşü burada ve discord dev de düzeltmek gerek
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


def create_jwt_token(user_id, username, email, roles, secret_key):
    # Token creation time
    issued_at = datetime.datetime.utcnow()

    # Token expiration time (for example, 30 days)
    expiration = issued_at + datetime.timedelta(days=30)

    # Generate unique jti using UUID
    unique_jti = str(uuid.uuid4())

    payload = {
        "iss": "horiarapi.com",   # Issuer
        "sub": user_id,           # Subject (user ID)
        "aud": "horiar_client",   # Audience
        "exp": expiration,        # Expiration time
        "iat": issued_at,         # Issued at time
        "jti": unique_jti,        # Unique ID
        "username": username,     # User's username
        "email": email,            # User's email
        "role": roles[0]
    }

    # Token oluşturma
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def verify_jwt_token(token, secret_key):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"], audience='horiar_client')

        # Gerekli alanların olup olmadığını kontrol et
        if "sub" not in payload or "username" not in payload:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token süresi dolmuş
    except jwt.InvalidTokenError:
        return None  # Geçersiz token


def jwt_required(pass_payload=False):
    """
    JWT doğrulaması yapan middleware.
    pass_payload: Eğer True ise payload fonksiyona geçilir.
    """
    def decorator(f):
        @wraps(f)
        def jwt_wrapper(*args, **kwargs):
            # OPTIONS isteklerinde JWT doğrulaması yapılmaz, isteği doğrudan geç
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)

            auth_header = request.headers.get('Authorization')
            if auth_header:
                token = auth_header.split(" ")[1]
            else:
                return jsonify({"message": "Token is missing!"}), 403

            payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])

            if payload is None:
                return jsonify({"message": "Token is invalid or expired!"}), 403

            if pass_payload:
                # Eğer pass_payload True ise, payload'u fonksiyona geçiriyoruz
                return f(payload, *args, **kwargs)
            else:
                # Eğer pass_payload False ise, payload'u geçirmeden fonksiyonu çağırıyoruz
                return f(*args, **kwargs)
        return jwt_wrapper
    return decorator



