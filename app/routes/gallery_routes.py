import uuid

from flask import Blueprint, jsonify, request, make_response
import logging

from app.models.galley_photo_model import GalleryPhoto

gallery_routes_bp = Blueprint('gallery_bp', __name__)

# 1. Veritabanında tutulmuş tüm gallery öğelerini almak
@gallery_routes_bp.route('/gallery-items', methods=['GET'])
def get_all_gallery_items():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))

        # Sayfalama ile gallery öğelerini alıyoruz
        gallery_items = GalleryPhoto.objects.skip((page - 1) * limit).limit(limit)
        total_items = GalleryPhoto.objects.count()
        total_pages = (total_items + limit - 1) // limit  # Toplam sayfa sayısını hesaplıyoruz

        # Gallery öğelerini JSON formatına dönüştürme
        items_list = [item.to_dict_for_frontend() for item in gallery_items]
        return jsonify({
            "items": items_list,
            "total_pages": total_pages,
            "current_page": page
        }), 200

    except Exception as e:
        logging.error(f"Error fetching gallery items: {e}")
        return jsonify({"error": str(e)}), 500

@gallery_routes_bp.route('/like', methods=['POST'])
def like_photo():
    try:
        user_id = request.form.get('user_id')
        photo_id = request.form.get('photo_id')

        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        # Kullanıcının daha önce beğenip beğenmediğini kontrol et
        if user_id in photo.liked_by_users:
            return jsonify({"message": "Bu fotoğrafı zaten beğenmişsiniz"}), 400

        # Kullanıcı beğenmediyse beğeni ekle
        photo.liked_by_users.append(user_id)
        photo.likes_count += 1
        photo.save()

        return jsonify({"message": "Fotoğraf başarıyla beğenildi"}), 200

    except Exception as e:
        logging.error(f"Error liking photo: {e}")
        return jsonify({"error": str(e)}), 500

@gallery_routes_bp.route('/unlike', methods=['POST'])
def unlike_photo():
    try:
        user_id = request.form.get('user_id')
        photo_id = request.form.get('photo_id')

        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        # Kullanıcının daha önce beğenip beğenmediğini kontrol et
        if user_id not in photo.liked_by_users:
            return jsonify({"message": "Bu fotoğrafı henüz beğenmemişsiniz"}), 400

        # Kullanıcı daha önce beğendiyse beğeniyi kaldır
        photo.liked_by_users.remove(user_id)
        photo.likes_count -= 1
        photo.save()

        return jsonify({"message": "Beğeni başarıyla kaldırıldı"}), 200

    except Exception as e:
        logging.error(f"Error unliking photo: {e}")
        return jsonify({"error": str(e)}), 500


@gallery_routes_bp.route('/view-photo', methods=['POST'])
def increment_photo_views():
    try:
        photo_id = request.form.get('photo_id')

        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        # Görüntülenme sayısını artır
        photo.views_count += 1
        photo.save()

        return jsonify({"message": "Fotoğraf görüntülenme sayısı güncellendi"}), 200

    except Exception as e:
        logging.error(f"Error incrementing photo views: {e}")
        return jsonify({"error": str(e)}), 500
