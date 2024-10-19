import os

from flask import send_from_directory

from app.routes.admin_routes import admin_routes_bp
from app.routes.coupon_routes import coupon_bp
from app.routes.enterprise.enterprise_routes import enterprise_bp
from app.routes.mail_routes import mail_bp
from app.routes.payment_routes import payment_bp
from app.routes.upscale_routes import upscale_bp
from app.routes.user_routes import user_bp
from app.routes.package_routes import package_bp
from app.routes.text_to_image_routes import text_to_image_bp

def register_blueprints(app):
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(package_bp, url_prefix='/package')
    app.register_blueprint(text_to_image_bp, url_prefix='/create')
    app.register_blueprint(upscale_bp, url_prefix='/upscale')
    app.register_blueprint(coupon_bp, url_prefix='/coupon')
    app.register_blueprint(mail_bp)
    app.register_blueprint(admin_routes_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(enterprise_bp, url_prefix='/enterprise')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')


