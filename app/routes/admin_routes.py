import logging
from datetime import datetime

from flask import render_template, redirect, url_for, flash, Blueprint, session, request, jsonify
from flask_login import login_user, logout_user

from app.auth import jwt_required
from app.models.coupon_model import Coupon
from app.models.discord_image_request_model import DiscordImageRequest
from app.models.image_request_model import ImageRequest
from app.models.package_model import Package
from app.models.subscription_model import Subscription
from app.models.text_to_image_model import TextToImage
from app.models.upscale_model import Upscale
from app.models.user_model import User
from app.services.coupon_service import CouponService
from app.services.user_service import UserService
from app.forms.forms import LoginForm

admin_routes_bp = Blueprint('admin_routes_bp', __name__)

# Dummy kullanıcı bilgileri (Bunları veritabanından alacak şekilde düzenleyebilirsiniz)
admin_users = {
    "admin": "hashed_password",  # Şifreyi hashlenmiş bir şekilde saklamalısınız
}

@admin_routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Kullanıcıyı veritabanında arıyoruz
        user = User.objects(username=form.username.data).first()

        # Kullanıcı varsa ve şifre doğruysa giriş başarılı olur
        if user and UserService.check_password(user.password, form.password.data):

            # Kullanıcının roles alanında ilgili rol var mı kontrol edelim
            admin_role = "9951a9b2-f455-4940-931e-432bc057179a"  # Admin rolü ID'si
            if admin_role in user.roles:  # Kullanıcıda bu rol var mı kontrol et
                login_user(user)  # Kullanıcıyı giriş yaptır
                session['admin_logged_in'] = True  # Admin oturumunu işaretle
                return redirect(url_for('admin.index'))  # Admin index sayfasına yönlendir
            else:
                flash('Admin yetkisine sahip değilsiniz.', 'danger')  # Rol yoksa hata mesajı

        # Eğer kullanıcı adı veya şifre hatalıysa flash mesajı göster
        flash('Yanlış kullanıcı adı veya şifre', 'danger')

    return render_template('admin_login.html', form=form)

@admin_routes_bp.route('/admin/logout')
def logout():
    logout_user()
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_routes_bp.login'))

@admin_routes_bp.route('/users')
def admin_users():
    # Tüm kullanıcıları veritabanından al
    users = UserService.get_all_users()
    return render_template('admin/users.html', users=users)

@admin_routes_bp.route('/image-requests')
def list_image_requests():
    # Veritabanından tüm ImageRequest nesnelerini çekiyoruz
    image_requests = TextToImage.objects()
    return render_template('admin/image_requests.html', image_requests=image_requests)

@admin_routes_bp.route('/upscale-requests')
def list_upscale_requests():
    # Veritabanından tüm ImageRequest nesnelerini çekiyoruz
    requests = Upscale.objects()
    return render_template('admin/upscale_requests.html', image_requests=requests)

@admin_routes_bp.route('/discord_requests')
def discord_requests():
    discord_requests = DiscordImageRequest.objects.all()  # Discord isteklerini al
    return render_template('admin/discord_requests.html', discord_requests=discord_requests)


"""
Admin Dashboard İçin Kupon Rotaları ------------------------------------------------------------------------------------
"""
@admin_routes_bp.route('/coupons')
def coupons():
    # Veritabanından tüm kuponları al
    coupons = Coupon.objects.all()
    return render_template('admin/coupon/coupons.html', coupons=coupons)

@admin_routes_bp.route('/coupons/new', methods=['GET', 'POST'])
def create_coupon():
    try:
        # Formdan gelen verileri al
        name = request.form.get('name')
        discount_percentage = float(request.form.get('discount_percentage'))
        valid_until = request.form.get('valid_until')
        max_usage = int(request.form.get('max_usage'))

        # Yeni kupon oluştur
        coupon = Coupon(
            name=name,
            discount_percentage=discount_percentage,
            valid_until=datetime.strptime(valid_until, '%Y-%m-%d'),
            max_usage=max_usage,
            is_active=True,  # Varsayılan olarak aktif durumda olacak
            usage_count=0     # Yeni kupon olduğundan kullanım sayısı 0
        )
        coupon.save()

        # Kupon oluşturulduktan sonra kuponlar sayfasına yönlendirme
        return redirect(url_for('admin_routes_bp.coupons'))

    except Exception as e:
        logging.error(f"Kupon oluşturulurken hata: {str(e)}")
        return render_template('admin/coupon/new_coupon.html', error=str(e))

@admin_routes_bp.route('/coupons/update-status', methods=['POST'])
def update_coupon_status():
    try:
        data = request.get_json()
        coupon_id = data.get('coupon_id')
        is_active = data.get('value')

        # Kuponu güncelle
        coupon = Coupon.objects(id=coupon_id).first()
        if not coupon:
            return jsonify({"message": "Kupon bulunamadı"}), 404

        coupon.update(is_active=is_active)

        return jsonify({"message": "Kupon durumu güncellendi"}), 200
    except Exception as e:
        logging.error(f"Kupon durumu güncellenirken hata: {str(e)}")
        return jsonify({"message": "Kupon durumu güncellenirken bir hata oluştu"}), 500

@admin_routes_bp.route('/coupons/delete', methods=['DELETE'])
def delete_coupon():
    try:
        data = request.get_json()
        coupon_id = data.get('coupon_id')

        # Coupon ID'nin varlığını kontrol et
        if not coupon_id:
            return jsonify({"error": "Coupon ID gerekli"}), 400

        # Kuponu sil
        deleted = CouponService.delete(coupon_id)
        if not deleted:
            return jsonify({"error": "Kupon bulunamadı veya silinemedi"}), 404

        return jsonify({"message": "Kupon başarıyla silindi"}), 200

    except Exception as e:
        return jsonify({"error": f"Kupon silinirken hata oluştu: {str(e)}"}), 500

@admin_routes_bp.route('/coupons/edit/<coupon_id>', methods=['GET', 'POST'])
def edit_coupon(coupon_id):
    try:
        # Kuponu veri tabanından al
        coupon = CouponService.get_by_id(coupon_id)

        if not coupon:
            flash('Kupon bulunamadı veya erişilemedi.', 'danger')
            return redirect(url_for('admin_routes_bp.coupons'))

        if request.method == 'POST':
            # Formdan gelen verileri al
            name = request.form.get('name')
            discount_percentage = request.form.get('discount_percentage')
            valid_until = request.form.get('valid_until')
            max_usage = request.form.get('max_usage')

            # Formda eksik alan var mı kontrol et
            if not all([name, discount_percentage, valid_until, max_usage]):
                flash('Lütfen tüm alanları doldurun.', 'danger')
                return render_template('admin/coupon/edit_coupon.html', coupon=coupon)

            # Geçerlilik süresi doğru formatta değilse uyarı ver
            try:
                valid_until = datetime.strptime(valid_until, '%Y-%m-%d')
            except ValueError:
                flash('Geçerlilik süresi hatalı bir formatta (YYYY-MM-DD olmalı).', 'danger')
                return render_template('admin/coupon/edit_coupon.html', coupon=coupon)

            # Kuponu güncelle
            updated_data = {
                'name': name,
                'discount_percentage': float(discount_percentage),
                'valid_until': valid_until,
                'max_usage': int(max_usage)
            }
            update_success = CouponService.update(coupon_id, **updated_data)

            if update_success:
                flash('Kupon başarıyla güncellendi.', 'success')
            else:
                flash('Kupon güncellenirken bir sorun oluştu.', 'danger')

            return redirect(url_for('admin_routes_bp.coupons'))

        return render_template('admin/coupon/edit_coupon.html', coupon=coupon)

    except Exception as e:
        flash(f'Kupon düzenlenirken bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('admin_routes_bp.coupons'))

"""
Admin Dashboard İçin Package Rotaları ------------------------------------------------------------------------------------
"""
@admin_routes_bp.route('/packages', methods=['GET'])
def list_packages():
    packages = Package.objects.all()
    return render_template('admin/package/packages.html', packages=packages)

@admin_routes_bp.route('/packages/new', methods=['GET', 'POST'])
def create_package():
    if request.method == 'POST':
        data = request.form
        title = data.get('title')
        monthly_original_price = float(data.get('monthly_original_price'))
        yearly_original_price = float(data.get('yearly_original_price'))
        monthly_sale_price = float(data.get('monthly_sale_price', 0)) if data.get('monthly_sale_price') else None
        yearly_sale_price = float(data.get('yearly_sale_price', 0)) if data.get('yearly_sale_price') else None
        features = data.getlist('features')

        try:
            package = Package(
                title=title,
                monthly_original_price=monthly_original_price,
                yearly_original_price=yearly_original_price,
                monthly_sale_price=monthly_sale_price,
                yearly_sale_price=yearly_sale_price,
                features=features
            )
            package.save()
            return redirect(url_for('admin_routes_bp.list_packages'))
        except Exception as e:
            logging.error(f"Paketi oluştururken hata: {e}")
            return jsonify({"error": "Paketi oluştururken hata oluştu."}), 500

    return render_template('admin/package/create_package.html')

@admin_routes_bp.route('/packages/edit/<package_id>', methods=['GET', 'POST'])
def edit_package(package_id):
    package = Package.objects(id=package_id).first()
    if not package:
        return redirect(url_for('admin_routes_bp.list_packages'))

    if request.method == 'POST':
        data = request.form
        package.title = data.get('title')
        package.monthly_original_price = float(data.get('monthly_original_price'))
        package.yearly_original_price = float(data.get('yearly_original_price'))
        package.monthly_sale_price = float(data.get('monthly_sale_price', 0)) if data.get('monthly_sale_price') else None
        package.yearly_sale_price = float(data.get('yearly_sale_price', 0)) if data.get('yearly_sale_price') else None
        package.features = data.getlist('features')

        try:
            package.save()
            return redirect(url_for('admin_routes_bp.list_packages'))
        except Exception as e:
            logging.error(f"Paketi güncellerken hata: {e}")
            return jsonify({"error": "Paketi güncellerken hata oluştu."}), 500

    return render_template('admin/package/edit_package.html', package=package)

@admin_routes_bp.route('/packages/delete/<package_id>', methods=['POST'])
def delete_package(package_id):
    try:
        package = Package.objects(id=package_id).first()
        if package:
            package.delete()
        return jsonify({"message": "Paket başarıyla silindi."}), 200
    except Exception as e:
        logging.error(f"Paket silinirken hata: {e}")
        return jsonify({"error": "Paket silinirken hata oluştu."}), 500


@admin_routes_bp.route('/send-mail-page', methods=['GET'])
def send_mail_page():
    users = User.objects()
    return render_template('admin/mail/send_mail.html', users=users)


"""
Admin Dashboard Rotaları ------------------------------------------------------------------------------------
"""

@admin_routes_bp.route('/dashboard')
def dashboard():
    subscription_count = Subscription.objects.count()
    web_site_users = User.objects.count()

    discord_requests = TextToImage.objects(source="discord")
    unique_discord_usernames = discord_requests.distinct('discord_username')
    distinct_discord_user_count = len(unique_discord_usernames)
    text_to_image_requests = TextToImage.objects(source="web").count()
    upscale_requets = Upscale.objects.count()

    # Başka istatistikler de eklenebilir
    return render_template('admin/dashboard.html', subscription_count=subscription_count,
                           web_site_users=web_site_users, distinct_discord_user_count=distinct_discord_user_count,
                           text_to_image_requests=text_to_image_requests, upscale_requets=upscale_requets)





