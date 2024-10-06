from flask import request, Blueprint, jsonify

from app.auth import jwt_required
from app.routes.admin_routes import admin_routes_bp
from app.utils.mail_utils import send_email
from marshmallow import Schema, fields, ValidationError
import markdown

mail_bp = Blueprint('mail_bp', __name__)


# Schema for validating incoming mail data
class MailSchema(Schema):
    recipients = fields.List(fields.Email(), required=True)
    subject = fields.Str(required=True)
    body = fields.Str(required=True)
    html_body = fields.Str(required=False)


@mail_bp.route('/send-mail', methods=['POST'])
@jwt_required(pass_payload=True)
def send_mail():
    try:
        # Validate incoming data with MailSchema
        schema = MailSchema()
        data = schema.load(request.json)

        # Send email using the validated data
        send_email(
            subject=data['subject'],
            recipients=data['recipients'],
            body=data['body'],
            html_body=data.get('html_body')
        )
        return jsonify({"message": "Mail sent successfully!"}), 200

    except ValidationError as err:
        return jsonify({"error": "Invalid data", "details": err.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_routes_bp.route('/admin-send-mail', methods=['POST'])
def admin_send_mail():
    data = request.get_json()
    subject = data.get('subject')
    recipients = data.get('recipients')  # Örneğin ["alavhasan72892@gmail.com"]
    body = data.get('body')
    html_body = data.get('html_body')

    print(recipients)

    # Eğer html_body boş ise, body'yi markdown olarak alıp HTML'e çeviriyoruz
    if html_body is None or html_body == "":
        html_body = markdown.markdown(body)

    try:
        send_email(
            subject=subject,
            recipients=recipients,
            body=body,
            html_body=html_body
        )
        return jsonify({"message": "Mail sent successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
