from flask import Blueprint, request, jsonify, current_app

from app.middlewares import api_key_required
from app.services.enterprise.enterprise_service import EnterpriseService

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
        return jsonify({"message": "Request has been queued", "job_id": job.id }), 200
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
    try:
        # İmajı request'ten almak
        if 'image' not in request.files:
            return jsonify({"error": "No image file part"}), 400

        image_file = request.files['image']
        # Eğer dosya ismi boş ise, kullanıcı dosya seçmemiş demektir
        if image_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if image_file:
            # Resim dosyasını istediğiniz işlemleri yapmak üzere okuyabilirsiniz
            image_bytes = image_file.read()  # Bu binary veriyi işlemek için kullanabilirsiniz

            # Yeni upscale isteği oluşturuluyor
            job = service.upscale(customer=customer, image_bytes=image_bytes, room=str(customer.id))

            return jsonify({"message": "Request has been queued", "job_id": job.id }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

    return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

@enterprise_bp.route('/image-to-video', methods=['POST'])
@api_key_required
def generate_image_to_video(customer):
    room = str(customer.id)
    prompt = request.form.get('prompt')

    if not prompt:
        return jsonify({"message": "Missing required fields"}), 400

    if 'image' not in request.files:
        return jsonify({"error": "No image file part"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if image_file:
        image_bytes = image_file.read()

        # Kuyruğa göre video generation işlemini başlatma
        job = EnterpriseService.image_to_video(prompt, customer, image_bytes, room)

        return jsonify({"message": "Request has been queued", "job_id": job.id, "room": room}), 200

    return 400


@enterprise_bp.route('/text-to-image', methods=['GET'])
@api_key_required
def get_text_to_images(customer):
    service = EnterpriseService()
    list = service.get_all_text_to_images(customer)
    return jsonify(list)


@enterprise_bp.route('/text-to-image-consistent', methods=['GET'])
@api_key_required
def get_text_to_images_consistent(customer):
    service = EnterpriseService()
    list = service.get_all_text_to_images_consistent(customer)
    return jsonify(list)


@enterprise_bp.route('/upscale-enhance', methods=['GET'])
@api_key_required
def get_upscale_enhances(customer):
    service = EnterpriseService()
    list = service.get_all_upscale_enhances(customer)
    return jsonify(list)

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

@enterprise_bp.route('/text-to-image-consistent/<request_id>', methods=['GET'])
@api_key_required
def get_one_text_to_images_consistent(customer, request_id):
    service = EnterpriseService()
    try:
        request = service.get_one_text_to_image_consistent(customer, request_id)
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