from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView

from app.models.coupon_model import Coupon
from app.models.image_request_model import ImageRequest
from app.models.user_model import User
from app.models.package_model import Package

class CouponView(ModelView):
    column_list = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage', 'usage_count', 'used_by')
    form_columns = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage')

    # 'used_by' alanını kullanıcı adları ile göstermek için column_formatter ekleyelim
    column_formatters = {
        'used_by': lambda v, c, m, p: ', '.join([user.username for user in m.used_by])  # Kullanıcı adlarını gösteriyoruz
    }

class ImageRequestView(ModelView):
    column_list = ('user_id', 'username', 'prompt', 'image', 'request_time')  # Görüntülenecek alanlar
    form_columns = (
    'user_id', 'username', 'prompt')  # Sadece gerekli alanları admin panelde düzenlenebilir yapıyoruz
    can_create = False  # Admin panelden yeni istek oluşturma kapalı
    can_edit = False  # Admin panelden düzenleme kapalı
    can_delete = True  # Admin panelde istekleri silebiliriz

class UserView(ModelView):
    column_list = ('email', 'username', 'is_active', 'is_banned')  # Görüntülenecek sütunlar
    form_columns = ('email', 'username', 'is_active', 'is_banned')  # Düzenlenebilir alanlar
    can_create = False  # Yeni kullanıcı oluşturma kapalı
    can_edit = True     # Kullanıcı düzenlenebilir
    can_delete = True   # Kullanıcı silinebilir

    # Aranabilir sütunlar
    searchable_columns = ['username']  # Kullanıcı adı üzerinden arama yapabilirsiniz


def configure_admin(app):
    # Flask-Admin'i başlat
    admin = Admin(app, name='Horiar Admin Paneli', template_mode='bootstrap3')
    # Modelleri admin paneline ekleyin
    admin.add_view(UserView(User))
    admin.add_view(ModelView(Package))
    admin.add_view(CouponView(Coupon))
    admin.add_view(ImageRequestView(ImageRequest))