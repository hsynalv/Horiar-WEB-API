from flask import request, current_app, redirect, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.mongoengine import ModelView

from app.auth import verify_jwt_token
from app.models.coupon_model import Coupon
from app.models.image_request_model import ImageRequest
from app.models.user_model import User
from app.models.package_model import Package

# Tüm admin paneli için global erişim kontrolü
class AdminBaseView(ModelView):
    def is_accessible(self):
        # JWT token'ı Authorization başlığından al
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return False  # Authorization başlığı yoksa erişimi engelle

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])

        # Kullanıcının rollerini kontrol ediyoruz
        if payload and 'admin' in payload.get('roles', []):
            return True

        return False  # Admin rolü olmayan kullanıcılar için erişim yok

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('user_bp.login'))  # Giriş sayfasına yönlendir
        pass

# Admin index view (Home sayfası) için de erişim kontrolü
class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        # JWT token'ı Authorization başlığından al
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return False  # Authorization başlığı yoksa erişimi engelle

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token, current_app.config['SECRET_KEY'])

        # Kullanıcının rollerini kontrol ediyoruz
        if payload and 'admin' in payload.get('roles', []):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('user_bp.login'))  # Giriş sayfasına yönlendir

# AdminBaseView'i kullanarak diğer view'leri türetelim
class CouponView(AdminBaseView):
    column_list = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage', 'usage_count', 'used_by')
    form_columns = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage')

    # 'used_by' alanını kullanıcı adları ile göstermek için column_formatter ekleyelim
    column_formatters = {
        'used_by': lambda v, c, m, p: ', '.join([user.username for user in m.used_by])  # Kullanıcı adlarını gösteriyoruz
    }

class ImageRequestView(AdminBaseView):
    column_list = ('user_id', 'username', 'prompt', 'image', 'request_time')  # Görüntülenecek alanlar
    form_columns = ('user_id', 'username', 'prompt')  # Sadece gerekli alanları admin panelde düzenlenebilir yapıyoruz
    can_create = False  # Admin panelden yeni istek oluşturma kapalı
    can_edit = False    # Admin panelden düzenleme kapalı
    can_delete = True   # Admin panelde istekleri silebiliriz

class UserView(AdminBaseView):
    column_list = ('email', 'username', 'is_active', 'is_banned')  # Görüntülenecek sütunlar
    form_columns = ('email', 'username', 'is_active', 'is_banned')  # Düzenlenebilir alanlar
    can_create = False  # Yeni kullanıcı oluşturma kapalı
    can_edit = True     # Kullanıcı düzenlenebilir
    can_delete = True   # Kullanıcı silinebilir

    # Aranabilir sütunlar
    searchable_columns = ['username']  # Kullanıcı adı üzerinden arama yapabilirsiniz

def configure_admin(app):
    # Flask-Admin'i başlat, AdminIndexView'i kullanarak home erişimini kontrol ediyoruz
    admin = Admin(app, name='Horiar Admin Paneli', template_mode='bootstrap3', index_view=AdminHomeView())

    # Modelleri admin paneline ekleyin
    admin.add_view(UserView(User))
    admin.add_view(AdminBaseView(Package))  # AdminBaseView'den türetildi
    admin.add_view(CouponView(Coupon))
    admin.add_view(ImageRequestView(ImageRequest))
