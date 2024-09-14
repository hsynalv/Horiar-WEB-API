from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView

from app.models.coupon_model import Coupon
from app.models.user_model import User
from app.models.package_model import Package

class CouponView(ModelView):
    column_list = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage', 'usage_count', 'used_by')
    form_columns = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage')

    # 'used_by' alanını kullanıcı adları ile göstermek için column_formatter ekleyelim
    column_formatters = {
        'used_by': lambda v, c, m, p: ', '.join([user.username for user in m.used_by])  # Kullanıcı adlarını gösteriyoruz
    }


def configure_admin(app):
    # Flask-Admin'i başlat
    admin = Admin(app, name='Horiar Admin Paneli', template_mode='bootstrap3')
    admin.add_view(CouponView(Coupon))
    # Modelleri admin paneline ekleyin
    admin.add_view(ModelView(User))
    admin.add_view(ModelView(Package))