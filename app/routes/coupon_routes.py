# /app/routes/coupon_routes.py
from flask import Blueprint, jsonify, request
from app.services.coupon_service import CouponService
from app.auth import jwt_required

coupon_bp = Blueprint('coupon_bp', __name__)

@coupon_bp.route('/use-coupon', methods=['POST'])
@jwt_required(pass_payload=True)  # JWT'den gelen payload'u alıyoruz
def use_coupon(payload):  # JWT'den gelen payload'u alıyoruz
    try:
        user_id = payload['sub']  # JWT'den gelen user_id'yi alıyoruz
        data = request.json
        coupon_name = data.get('coupon_name')  # Kupon adını body'den alıyoruz

        if not coupon_name:
            return jsonify({"message": "Coupon name is required"}), 400
        print(coupon_name)

        coupon = CouponService.use_coupon(coupon_name, user_id)  # Kuponu kullanıyoruz
        return jsonify({"message": "Coupon used successfully", "coupon": coupon}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@coupon_bp.route('/check-coupon', methods=['POST'])
@jwt_required(pass_payload=True)
def check_coupon(payload):
    try:
        data = request.json
        coupon_name = data.get('coupon_name')  # Kupon adını body'den alıyoruz

        if not coupon_name:
            return jsonify({"message": "Coupon name is required"}), 400

        coupon = CouponService.check_coupon(coupon_name, payload)  # Kuponu kontrol ediyoruz
        return jsonify({"message": "Coupon found", "coupon": coupon}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500