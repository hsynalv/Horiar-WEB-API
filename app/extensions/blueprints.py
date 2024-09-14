from app.routes.coupon_routes import coupon_bp
from app.routes.user_routes import user_bp
from app.routes.package_routes import package_bp
from app.routes.text_to_image_routes import text_to_image_bp

def register_blueprints(app):
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(package_bp, url_prefix='/package')
    app.register_blueprint(text_to_image_bp, url_prefix='/create')
    app.register_blueprint(coupon_bp, url_prefix='/coupon')
