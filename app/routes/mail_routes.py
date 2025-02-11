from flask import request, Blueprint, jsonify
import requests

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
    external_url = "http://3.68.189.144:3000/send-email"
    
    recipients = data.get('recipients', [])
    body = data.get('body', '')
    html_body = data.get('html_body', '')
    if not html_body:
        html_body = markdown.markdown(body)

    print(f"body: {body}")
    print(f"html_body: {html_body}")

    errors = []
    for email in recipients:
        name = email.split('@')[0]
        payload = {
            "email": email,
            "type": "announcement", 
            "data": {
                "name": name,
                "message": html_body
            }
        }
        try:
            response = requests.post(external_url, json=payload)
            response.raise_for_status()
        except Exception as e:
            errors.append({"email": email, "error": str(e)})
            
    if errors:
        return jsonify({"error": "Some emails failed.", "details": errors}), 500
    return jsonify({"message": "Mail sent successfully!"}), 200
