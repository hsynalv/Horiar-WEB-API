from flask import Blueprint, request, jsonify
from app.services.text_to_image import TextToImageService
import requests

text_to_image_bp = Blueprint('text_to_image', __name__)

@text_to_image_bp.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Text to image servisinden görseli oluşturma
        image_data = TextToImageService.generate_image_from_text(prompt)
        return jsonify(image_data), 200
    except requests.HTTPError as http_err:
        return jsonify({"message": str(http_err)}), 500
