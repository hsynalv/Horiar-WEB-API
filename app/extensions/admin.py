import logging

from flask import redirect, session, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.contrib.mongoengine.filters import FilterEqual
from flask_admin.form import Select2Widget
from wtforms import widgets
from wtforms.fields.choices import SelectMultipleField

from app.models.coupon_model import Coupon
from app.models.discord_image_request_model import DiscordImageRequest
from app.models.feature_model import Feature
from app.models.image_request_model import ImageRequest
from app.models.user_model import User
from app.models.package_model import Package

# Tüm admin paneli için global erişim kontrolü
class AdminBaseView(ModelView):
    def is_accessible(self):
        # `session`'da `admin_logged_in` işaretini kontrol ediyoruz
        if session.get('admin_logged_in'):
            return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_auth_bp.login'))

class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_auth_bp.login'))


# AdminBaseView'i kullanarak diğer view'leri türetelim
class CouponView(AdminBaseView):
    column_list = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage', 'usage_count', 'used_by')
    form_columns = ('name', 'discount_percentage', 'valid_until', 'is_active', 'max_usage')

    # Kolon başlıklarını özelleştirme
    column_labels = {
        'name': 'Kupon Adı',
        'discount_percentage': 'İndirim Oranı',
        'valid_until': 'Geçerlilik Süresi',
        'is_active': 'Aktif mi?',
        'max_usage': 'Kullanım Sınırı',
        'usage_count': 'Kullanım Sayısı',
        'used_by': 'Kuponu Kullananlar'
    }

    # 'used_by' alanını kullanıcı adları ile göstermek için column_formatter ekleyelim
    column_formatters = {
        'used_by': lambda v, c, m, p: ', '.join([user.username for user in m.used_by])  # Kullanıcı adlarını gösteriyoruz
    }

class ImageRequestView(AdminBaseView):
    column_list = ('user_id', 'username', 'prompt', 'image', 'request_time')  # Görüntülenecek alanlar
    form_columns = ('user_id', 'username', 'prompt')  # Sadece gerekli alanları admin panelde düzenlenebilir yapıyoruz

    # Kolon başlıklarını özelleştirme
    column_labels = {
        'user_id': 'User Id',
        'username': 'User Name',
    }

    can_create = False  # Admin panelden yeni istek oluşturma kapalı
    can_edit = False    # Admin panelden düzenleme kapalı
    can_delete = True   # Admin panelde istekleri silebiliriz

class UserView(AdminBaseView):
    column_list = ('email', 'username', 'is_enabled', 'is_banned')
    form_columns = ('email', 'username', 'is_enabled', 'is_banned')   # Düzenlenebilir alanlar
    can_create = False  # Yeni kullanıcı oluşturma kapalı
    can_edit = True     # Kullanıcı düzenlenebilir
    can_delete = True   # Kullanıcı silinebilir

    # Kolon başlıklarını özelleştirme
    column_labels = {
        'email': 'E-Mail',
        'username': 'User Name',
        'is_active': 'Aktiflik Durumu',
        'is_banned': 'Ban Durumu'
    }

    # Aranabilir sütunlar
    searchable_columns = ['username']  # Kullanıcı adı üzerinden arama yapabilirsiniz

# Sunucu adlarına göre dinamik listeleme filtresi
class GuildFilter(FilterEqual):
    def apply(self, query, value, alias=None):
        return query.filter(guild=value)

    def operation(self):
        return 'Sunucu Adı'

    def get_options(self, view):
        # Veritabanındaki benzersiz sunucu adlarını al
        guilds = DiscordImageRequest.objects.distinct('guild')
        return [(guild, guild) for guild in guilds]


# Admin View'a tarih filtresi ekliyoruz
class DiscordImageRequestView(AdminBaseView):
    column_list = ('user_id', 'username', 'prompt', 'datetime', 'guild', 'channel')  # Gösterilecek alanlar
    form_columns = ('user_id', 'username', 'prompt', 'datetime', 'guild', 'channel')  # Düzenlenebilir alanlar
    can_create = False  # Yeni kayıt ekleme kapalı
    can_edit = False    # Düzenleme kapalı
    can_delete = True   # Sadece silme işlemi aktif

    # Kolon başlıklarını özelleştirme
    column_labels = {
        'user_id': 'User Id',
        'username': 'User Name',
        'guild': 'Sunucu Adı',
        'datetime': 'Tarih'
    }

    # Sunucu adına göre sıralama ekliyoruz
    column_sortable_list = ['guild', 'datetime']  # Sunucu adına göre sıralanabilir liste

    # Dinamik sunucu adı filtresi ve tarih aralığı filtresi ekliyoruz
    column_filters = [
        GuildFilter(column=DiscordImageRequest.guild, name='Sunucu Adı')
    ]


class PackageView(AdminBaseView):
    # Görüntülenecek alanlar
    column_list = (
        'title',
        'monthly_original_price',
        'yearly_original_price',
        'monthly_sale_price',
        'yearly_sale_price',
        'features'
    )

    # Düzenlenebilir alanlar
    form_columns = (
        'title',
        'monthly_original_price',
        'yearly_original_price',
        'monthly_sale_price',
        'yearly_sale_price',
        'features'
    )

    can_create = True  # Admin panelden yeni paket eklenebilir
    can_edit = True  # Admin panelde paket düzenlenebilir
    can_delete = True  # Admin panelde paket silinebilir

    # Kolon başlıklarını özelleştirme
    column_labels = {
        'title': 'Paket Başlığı',
        'monthly_original_price': 'Aylık Orijinal Fiyat',
        'yearly_original_price': 'Yıllık Orijinal Fiyat',
        'monthly_sale_price': 'Aylık İndirimli Fiyat',
        'yearly_sale_price': 'Yıllık İndirimli Fiyat',
        'features': 'Özellikler'
    }

    # Sıralanabilir alanlar
    column_sortable_list = [
        'title',
        'monthly_original_price',
        'yearly_original_price',
        'monthly_sale_price',
        'yearly_sale_price'
    ]

def configure_admin(app):
    # Flask-Admin'i başlat, AdminIndexView'i kullanarak home erişimini kontrol ediyoruz
    admin = Admin(app, name='Horiar Admin Paneli', template_mode='bootstrap3', index_view=AdminHomeView())

    # Modelleri admin paneline ekleyin
    admin.add_view(UserView(User, name="Kullanıcılar"))
    admin.add_view(CouponView(Coupon, name="Kuponlar"))
    admin.add_view(ImageRequestView(ImageRequest, name='Web Site Requests'))
    admin.add_view(DiscordImageRequestView(DiscordImageRequest,  name='Discord Bot Requests'))
    admin.add_view(PackageView(Package, name="Paketler"))  # AdminBaseView'den türetildi
