from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import pytz

from app.auth import verify_jwt_token
from app.models.enterprise.enterprise_customer_model import EnterpriseCustomer
from app.models.image_request_model import ImageRequest  # MongoEngine modelini içe aktar
from app.models.user_model import User
from app.services.enterprise.enterprise_service import EnterpriseService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService


def daily_request_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # JWT'den kullanıcı bilgilerini alalım
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Token is missing!"}), 403

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])
        if payload is None:
            return jsonify({"message": "Invalid or expired token!"}), 403

        # user_id'yi string formatında alıyoruz
        user_id = payload.get('sub')

        # UTC'ye göre bugünün başlangıcı ve bitişi
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Log ekle: user_id ve zaman aralıklarını yazdır
        print(f"user_id: {user_id}, today_start (UTC): {today_start}, today_end (UTC): {today_end}")

        # Veritabanında bugünkü istekleri say - MongoEngine kullanarak
        request_count = ImageRequest.objects(
            user_id=user_id,
            request_time__gte=today_start,
            request_time__lt=today_end
        ).count()

        # Bugün yapılan istek sayısını logla
        print(f"Today's request count for user {user_id}: {request_count}")

        # Eğer istek sayısı 15'ten büyükse 401 döndür
        if request_count >= 15:
            return jsonify({"message": "Daily request limit exceeded!"}), 401

        # İstek sınırını geçmemişse, fonksiyonu çalıştır
        return f(*args, **kwargs)

    return decorated_function

def ban_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Token is missing!"}), 403

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])
        if payload is None:
            return jsonify({"message": "Invalid or expired token!"}), 403

        # Kullanıcıyı kontrol et
        user = User.objects(id=payload['sub']).first()
        if not user:
            return jsonify({"message": "User not found!"}), 404

        # Kullanıcının banlı olup olmadığını kontrol et
        if user.is_banned:
            return jsonify({"message": "User is banned!"}), 403

        return f(*args, **kwargs)

    return decorated_function
def check_credits(required_credits: int):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # JWT'den kullanıcı bilgilerini alalım
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({"message": "Token is missing!"}), 403

            token = auth_header.split(" ")[1]
            payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])
            if payload is None:
                return jsonify({"message": "Invalid or expired token!"}), 403

            # user_id'yi string formatında alıyoruz
            user_id = payload.get('sub')
            user = UserService.get_user_by_id(user_id)
            subscription = SubscriptionService.get_subscription_by_id(user_id)

            # Fonksiyonu çalıştır
            result = f(*args, **kwargs)

            # Fonksiyon başarılı bir şekilde çalıştıysa kredi kontrolü yap
            if isinstance(result, tuple) and result[1] == 200:  # Eğer başarılı bir sonuç dönerse
                if subscription is None:
                    if user.base_credits < required_credits:
                        return jsonify({"message": "Your credit is insufficient. Please buy a pack"}), 403
                    user.base_credits -= required_credits
                    user.save()
                else:
                    if subscription.credit_balance < required_credits:
                        return jsonify({"message": "Insufficient credits!"}), 403
                    subscription.credit_balance -= required_credits
                    subscription.save()

            return result  # Sonucu döndür

        return decorated_function
    return decorator

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            api_key = auth_header.split(" ")[1]
        else:
            return jsonify({"message": "API key is missing"}), 401

        customer = EnterpriseCustomer.objects(api_key=api_key).first()
        if not customer:
            return jsonify({"message": "Invalid API key"}), 401

        # Müşteri objesini route fonksiyonuna parametre olarak geçiyoruz
        return f(customer, *args, **kwargs)
    return decorated_function

