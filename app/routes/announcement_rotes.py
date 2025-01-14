from flask import Blueprint, request, jsonify

from app.services.announcement_service import AnnouncementService

announcement_bp = Blueprint('announcement_routes', __name__)

@announcement_bp.route('/add', methods=['POST'])
def create_announcement():
    """
    Yeni bir duyuru oluşturur.
    """
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        tags = request.form.getlist('tags')
        is_published = request.form.get('is_published', 'true').lower() == 'true'
        image_file = request.files.get('image')

        if not title or not content:
            return jsonify({"error": "Başlık ve içerik zorunludur"}), 400

        announcement = AnnouncementService.create_announcement(
            title=title,
            content=content,
            image_file=image_file,
            tags=tags,
            is_published=is_published
        )
        return jsonify({"message": "Duyuru başarıyla oluşturuldu", "announcement_id": str(announcement.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@announcement_bp.route('/<announcement_id>', methods=['PUT'])
def update_announcement(announcement_id):
    """
    Mevcut bir duyuruyu günceller.
    """
    try:
        updates = {
            "title_tr": request.form.get('title'),
            "title_en": AnnouncementService.translatePrompt(request.form.get('title')),
            "content_tr": request.form.get('content'),
            "content_en": AnnouncementService.translatePrompt(request.form.get('content')),
            "tags": request.form.get('tags', '').split(','),
            "is_published": request.form.get('is_published', 'true').lower() == 'true'
        }

        updated_announcement = AnnouncementService.update_announcement(announcement_id, **updates)
        return jsonify({"message": "Duyuru başarıyla güncellendi", "announcement_id": str(updated_announcement.id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@announcement_bp.route('/get/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    """
    Tek bir duyuruyu getirir.
    """
    try:
        announcement = AnnouncementService.get_announcement(announcement_id)
        return jsonify({
            "id": announcement_id,
            "title_tr": announcement.title_tr,
            "title_en": announcement.title_en,
            "content_tr": announcement.content_tr,
            "content_en": announcement.content_en,
            "image_url": announcement.image_url,
            "tags": announcement.tags,
            "is_published": announcement.is_published,
            "created_at": announcement.created_at.isoformat()
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@announcement_bp.route('/getall', methods=['GET'])
def get_all_announcements():
    """
    Tüm duyuruları getirir. Yayın durumuna göre filtreleme yapılabilir.
    """
    try:
        is_published = request.args.get('is_published')
        is_published = is_published.lower() == 'true' if is_published else None

        announcements = AnnouncementService.get_all_announcements(is_published=is_published)
        response = [
            {
                "id": str(announcement.id),
                "title_tr": announcement.title_tr,
                "title_en": announcement.title_en,
                "content_tr": announcement.content_tr,
                "content_en": announcement.content_en,
                "image_url": announcement.image_url,
                "tags": announcement.tags,
                "is_published": announcement.is_published,
                "created_at": announcement.created_at.isoformat()
            }
            for announcement in announcements
        ]
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@announcement_bp.route('/delete/<announcement_id>', methods=['DELETE'])
def delete_announcements(announcement_id):
    """
    Tüm duyuruları getirir. Yayın durumuna göre filtreleme yapılabilir.
    """
    try:
        result = AnnouncementService.delete(announcement_id)
        print(result)
        return "OK", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


