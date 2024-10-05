from flask import Blueprint, jsonify

from app.auth import jwt_required
from app.utils.mail_utils import send_email

mail_bp = Blueprint('mail_bp', __name__)

@mail_bp.route('/send-mail', methods=['GET'])
@jwt_required(pass_payload=False)
def send_test_mail():
    try:
        send_email(
            subject="Test Mail",
            recipients=["alavhasan72892@gmail.com"],
            body="This is a test mail from Flask.",
            html_body="<p>This is a <strong>test</strong> mail from Flask.</p>"
        )
        return jsonify({"message": "Mail sent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
