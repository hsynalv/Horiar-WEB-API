from flask import Blueprint, request, jsonify, current_app
from app.services.text_to_image import TextToImageService

text_to_image_bp = Blueprint('text_to_image', __name__)

@text_to_image_bp.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Text to image kuyruğuna ekle ve sonucu bekle
        result = TextToImageService.add_to_queue(current_app._get_current_object(), prompt)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
