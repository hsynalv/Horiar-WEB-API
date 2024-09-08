from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import pytz

from app.auth import verify_jwt_token


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

        # Veritabanında bugünkü istekleri say
        requests_collection = current_app.db["image_requests"]
        request_count = requests_collection.count_documents({
            "user_id": user_id,
            "request_time": {"$gte": today_start, "$lt": today_end}
        })

        # Bugün yapılan istek sayısını logla
        print(f"Today's request count for user {user_id}: {request_count}")

        # Eğer istek sayısı 15'ten büyükse 403 döndür
        if request_count >= 15:
            return jsonify({"message": "Daily request limit exceeded!"}), 403

        # İstek sınırını geçmemişse, fonksiyonu çalıştır
        return f(*args, **kwargs)

    return decorated_function
