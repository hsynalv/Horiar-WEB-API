import logging

from flask import Blueprint, request, jsonify, current_app

from app.middlewares import api_key_required
from app.services.enterprise.enterprise_service import EnterpriseService
from app.utils.convert_to_webp import download_image

enterprise_bp = Blueprint('enterprise_bp', __name__)


# Endpoint fonksiyonu
@enterprise_bp.route('/create-customer', methods=['POST'])
def create_enterprise_customer():
    service = EnterpriseService()

    # İstekten gelen veriyi al
    customer_data = request.json

    # Gerekli alanları kontrol et
    required_fields = ['company_name', 'contact_email']
    for field in required_fields:
        if field not in customer_data:
            return jsonify({"message": f"{field} is required"}), 400

    # Müşteri oluşturma işlemi
    try:
        new_customer = service.create_customer(customer_data)
        return jsonify({"message": "Customer created successfully", "customer": new_customer}), 201
    except Exception as e:
        return jsonify({"message": "Error creating customer", "error": str(e)}), 400

@enterprise_bp.route('/create-token', methods=['POST'])
def create_token():
    service = EnterpriseService()

    # İstekten gelen veriyi al
    data = request.json
    customer_id = data.get("customer_id")

    # Gerekli alan kontrolü
    if not customer_id:
        return jsonify({"message": "customer_id is required"}), 400

    # Token oluşturma işlemi
    try:
        api_key = service.create_token(customer_id)
        return jsonify({"message": "API key created successfully", "api_key": api_key}), 201
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 404  # Müşteri bulunamazsa
    except Exception as e:
        return jsonify({"message": "Error creating API key", "error": str(e)}), 400

# -------------------------------- Generate Request -------------------------------------------------------------------

@enterprise_bp.route('/text-to-image', methods=['POST'])
@api_key_required
def text_to_image(customer):
    service = EnterpriseService()
    data = request.json
    prompt = data.get('prompt')
    model_type = data.get('model_type', None)
    resolution = data.get('resolution', None)
    consistent = data.get('resolution', None)

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Text to image işlemini kuyruk kullanmadan doğrudan yap
        job = service.text_to_image(prompt_fix=True, model_type=model_type, resolution=resolution, customer=customer,
                                       consistent=consistent, prompt=prompt, room=str(customer.id))
        # Eğer result JSON değilse, burada hata olabilir
        return job, 200
    except Exception as e:
        print(f"Error: {e}")  # Hata mesajı
        return jsonify({"message": str(e)}), 500
    pass

@enterprise_bp.route('/upscale-enhance', methods=['POST'])
@api_key_required
def upscale_enhance(customer):
    service = EnterpriseService()
    """
       Yeni bir upscale talebi oluşturur.
       Bu rota, front-end'den gelen düşük çözünürlüklü bir resmi alır ve upscale işlemini başlatır.
       """
    room = str(customer.id)
    image_file = request.files.get('image')
    image_link = request.form.get('link')
    image_base64 = request.form.get('base64')

    # image_file, image_link ve image_base64 alanlarının yalnızca bir tanesinin dolu olmasını kontrol etme
    filled_fields = sum(bool(field) for field in [image_file, image_link, image_base64])
    logging.info(filled_fields)

    if filled_fields == 0:
        return jsonify({"error": "At least one image source must be provided"}), 400

    if filled_fields > 1:
        return jsonify({"error": "Only one image source can be provided at a time"}), 400

    # image_bytes oluşturma
    image_bytes = None

    try:
        if image_file:
            # Eğer image_file doluysa, dosyadan image_bytes oluştur
            if image_file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            image_bytes = image_file.read()

        elif image_link:
            # Eğer image_link doluysa, getS3 metodunu kullanarak resmi indir
            bytes_IO = download_image(image_link)
            image_bytes = bytes_IO.getvalue()

            if not image_bytes:
                return jsonify({"error": "Could not download image from link"}), 400

        elif image_base64:
            # Eğer image_base64 doluysa, base64 stringini image_bytes'a dönüştür
            try:
                image_bytes = base64.b64decode(image_base64)
            except:
                return jsonify({"error": "Invalid base64 image data"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if image_bytes:
        # Kuyruğa göre video generation işlemini başlatma
        job = service.upscale(customer=customer, image_bytes=image_bytes, room=str(customer.id))
        return job, 200

    return jsonify({"error": "An unexpected error occurred"}), 500


@enterprise_bp.route('/text-to-video', methods=['POST'])
@api_key_required
def generate_text_to_video(customer):
    data = request.json

    room = str(customer.id)
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    # Kuyruğa göre video generation işlemini başlatma
    job = EnterpriseService.text_to_video(prompt, customer, room)

    return job, 200
import base64


@enterprise_bp.route('/image-to-video', methods=['POST'])
@api_key_required
def generate_image_to_video(customer):
    room = str(customer.id)
    prompt = request.form.get('prompt')
    image_file = request.files.get('image')
    image_link = request.form.get('link')
    image_base64 = request.form.get('base64')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    # image_file, image_link ve image_base64 alanlarının yalnızca bir tanesinin dolu olmasını kontrol etme
    filled_fields = sum(bool(field) for field in [image_file, image_link, image_base64])
    logging.info(filled_fields)

    if filled_fields == 0:
        return jsonify({"error": "At least one image source must be provided"}), 400

    if filled_fields > 1:
        return jsonify({"error": "Only one image source can be provided at a time"}), 400

    # image_bytes oluşturma
    image_bytes = None

    try:
        if image_file:
            # Eğer image_file doluysa, dosyadan image_bytes oluştur
            if image_file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            image_bytes = image_file.read()

        elif image_link:
            # Eğer image_link doluysa, getS3 metodunu kullanarak resmi indir
            bytes_IO = download_image(image_link)
            image_bytes = bytes_IO.getvalue()

            if not image_bytes:
                return jsonify({"error": "Could not download image from link"}), 400

        elif image_base64:
            # Eğer image_base64 doluysa, base64 stringini image_bytes'a dönüştür
            try:
                image_bytes = base64.b64decode(image_base64)
            except:
                return jsonify({"error": "Invalid base64 image data"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if image_bytes:
        # Kuyruğa göre video generation işlemini başlatma
        job = EnterpriseService.image_to_video(prompt, customer, image_bytes, room)
        return job, 200

    return jsonify({"error": "An unexpected error occurred"}), 500

# -------------------------------- Get All Requests -------------------------------------------------------------------

@enterprise_bp.route('/text-to-image', methods=['GET'])
@api_key_required
def get_all_text_to_images(customer):
    service = EnterpriseService()
    list = service.get_all_text_to_images(customer)
    return jsonify(list)


@enterprise_bp.route('/upscale-enhance', methods=['GET'])
@api_key_required
def get_all_upscale_enhances(customer):
    service = EnterpriseService()
    list = service.get_all_upscale_enhances(customer)
    return jsonify(list)

@enterprise_bp.route('/text-to-video', methods=['GET'])
@api_key_required
def get_all_text_to_video(customer):
    service = EnterpriseService()
    try:
        request = service.get_all_text_to_video(customer)
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

@enterprise_bp.route('/image-to-video', methods=['GET'])
@api_key_required
def get_all_image_to_video(customer):
    service = EnterpriseService()
    try:
        request = service.get_all_image_to_video(customer)
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

# --------------------------------- Get One Requests -------------------------------------------------------------------

@enterprise_bp.route('/text-to-image/<request_id>', methods=['GET'])
@api_key_required
def get_one_text_to_image(customer, request_id):
    service = EnterpriseService()
    try:
        request = service.get_one_text_to_image(customer, request_id)
        if not request:
            return jsonify({"message": "Request not found"}), 404
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

@enterprise_bp.route('/text-to-video/<request_id>', methods=['GET'])
@api_key_required
def get_one_text_to_video(customer, request_id):
    service = EnterpriseService()
    try:
        request = service.get_one_text_to_video(customer, request_id)
        if not request:
            return jsonify({"message": "Request not found"}), 404
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

@enterprise_bp.route('/image-to-video/<request_id>', methods=['GET'])
@api_key_required
def get_one_image_to_video(customer, request_id):
    service = EnterpriseService()
    try:
        request = service.get_one_image_to_video(customer, request_id)
        if not request:
            return jsonify({"message": "Request not found"}), 404
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500


@enterprise_bp.route('/upscale-enhance/<request_id>', methods=['GET'])
@api_key_required
def get_one_upscale_enhance(customer, request_id):
    service = EnterpriseService()
    try:
        request = service.get_one_upscale_enhance(customer, request_id)
        if not request:
            return jsonify({"message": "Request not found"}), 404
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

@enterprise_bp.route('/query/<job_id>', methods=['GET'])
@api_key_required
def query_job_id(customer, job_id):
    service = EnterpriseService()
    try:
        request = service.get_query_job_id(customer, job_id)
        if not request:
            return jsonify({"message": "Request not found"}), 404
        return jsonify(request), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500
