from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView
from app.models.user_model import User
from app.models.package_model import Package

def configure_admin(app):
    # Flask-Admin'i başlat
    admin = Admin(app, name='Horiar Admin Paneli', template_mode='bootstrap3')

    # Modelleri admin paneline ekleyin
    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Package))
