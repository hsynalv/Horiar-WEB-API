import logging
from datetime import datetime, timedelta

from bson import ObjectId
from flask import render_template, redirect, url_for, flash, Blueprint, session, request, jsonify
from flask_login import login_user, logout_user

from app.models.coupon_model import Coupon
from app.models.discord_image_request_model import DiscordImageRequest
from app.models.image_to_video_model import ImageToVideo
from app.models.package_model import Package
from app.models.subscription_model import Subscription
from app.models.text_to_image_model import TextToImage
from app.models.text_to_video_model import TextToVideoGeneration
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

@admin_routes_bp.before_request
def require_admin_login():
    if not session.get('admin_logged_in') and request.endpoint != 'admin_routes_bp.login':
        flash('Bu sayfayı görmek için giriş yapmanız gerekiyor!', 'warning')
        return redirect(url_for('admin_routes_bp.login'))

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

@admin_routes_bp.route('/text-to-video-requests')
def list_text_to_video_requests():
    # Veritabanından tüm ImageRequest nesnelerini çekiyoruz
    requests = TextToVideoGeneration.objects()
    return render_template('admin/list_request/text_to_video_requests.html', video_requests=requests)


@admin_routes_bp.route('/upscale-requests')
def list_upscale_requests():
    # Veritabanından tüm ImageRequest nesnelerini çekiyoruz
    requests = Upscale.objects()
    return render_template('admin/upscale_requests.html', image_requests=requests)


@admin_routes_bp.route('/discord_requests')
def discord_requests():
    discord_requests = DiscordImageRequest.objects.all()  # Discord isteklerini al
    return render_template('admin/discord_requests.html', discord_requests=discord_requests)


@admin_routes_bp.route('/subscriptions')
def list_subscription():
    requests = Subscription.objects()
    return render_template('admin/subscription/subscription.html', subscription_requests=requests)


@admin_routes_bp.route('/get-user-by-email', methods=['POST'])
def get_user_by_email():
    email = request.json.get('email')
    user = User.objects(email=email).first()
    if user:
        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
    else:
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404


@admin_routes_bp.route('/assign-credit', methods=['POST'])
def assign_credit():
    """
    Kullanıcıya kredi tanımlama işlemini gerçekleştirir.
    """
    try:
        # İstekten JSON verilerini al
        data = request.get_json()
        user_id = data.get('user_id')
        credit = data.get('credit')
        expiry_date = data.get('expiry_date')

        # User ID ile veritabanından kullanıcıyı sorgula (örneğin User modelini kullanarak)
        # (Bu kısımda mevcut bir kullanıcıyı doğrulamak isteyebilirsiniz.)
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404

        # Subscription nesnesini oluştur
        subscription = Subscription(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            subscription_date=datetime.utcnow(),
            subscription_end_date=datetime.strptime(expiry_date, '%Y-%m-%d'),
            credit_balance=float(credit),
            merchant_oid="HORIAR-KREDI-TANIMLAMA",  # Manuel eklemelerde özel bir tanımlama
            used_coupon=None,  # İsteğe bağlı olarak kullanılabilir,
            max_credit_balance = int(credit)
        )

        # Yeni abonelik kaydını veritabanına kaydet
        subscription.save()

        return jsonify({"success": True, "message": "Kredi başarıyla tanımlandı!"}), 200

    except Exception as e:
        logging.error(f"Kredi tanımlama hatası: {str(e)}")
        return jsonify({"success": False, "message": "Kredi tanımlama sırasında bir hata oluştu"}), 500

"""
Admin Dashboard İçin Kupon Rotaları ------------------------------------------------------------------------------------
"""


@admin_routes_bp.route('/coupons')
def coupons():
    # Veritabanından tüm kuponları al
    coupons = Coupon.objects.all()

    # Kullanıcı id'leri üzerinden kullanıcı adlarını çekmek için bir sözlük
    user_ids = []
    for coupon in coupons:
        for user in coupon.used_by:
            # Eğer user nesnesi `User` ise user.id'yi alıyoruz, değilse doğrudan user_id'yi ekliyoruz
            user_ids.append(user.id if isinstance(user, User) else user)

    # Kullanıcı id'lerini ObjectId formatına çeviriyoruz (eğer değilse)
    user_ids = [ObjectId(user_id) for user_id in user_ids if isinstance(user_id, (str, ObjectId))]

    # Veritabanından kullanıcıları çekiyoruz
    users = User.objects(id__in=user_ids)
    users_dict = {str(user.id): user.username for user in
                  users}  # Kullanıcı id'leri ve adlarını bir sözlükte topluyoruz

    # Her bir kupon için kullanıcı bilgilerini ekleyin
    for coupon in coupons:
        coupon.used_by_usernames = [users_dict.get(str(user.id if isinstance(user, User) else user)) for user in
                                    coupon.used_by]

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

        # Yeni 'features' alanını iki dilde alıyoruz
        features_en = {f"feature_{i + 1}": val for i, val in enumerate(data.getlist('features_en'))}
        features_tr = {f"feature_{i + 1}": val for i, val in enumerate(data.getlist('features_tr'))}
        features = {
            "en": features_en,
            "tr": features_tr
        }

        try:
            package = Package(
                title=title,
                monthly_original_price=monthly_original_price,
                yearly_original_price=yearly_original_price,
                monthly_sale_price=monthly_sale_price,
                yearly_sale_price=yearly_sale_price,
                features=features  # Özellikler iki dilde ekleniyor
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
        package.monthly_sale_price = float(data.get('monthly_sale_price', 0)) if data.get(
            'monthly_sale_price') else None
        package.yearly_sale_price = float(data.get('yearly_sale_price', 0)) if data.get('yearly_sale_price') else None

        # Yeni 'features' alanını iki dilde alıyoruz
        features_en = {f"feature_{i + 1}": val for i, val in enumerate(data.getlist('features_en'))}
        features_tr = {f"feature_{i + 1}": val for i, val in enumerate(data.getlist('features_tr'))}
        package.features = {
            "en": features_en,
            "tr": features_tr
        }

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
    text_to_video = TextToVideoGeneration.objects.count()
    image_to_video = ImageToVideo.objects.count()

    # Başka istatistikler de eklenebilir
    return render_template('admin/dashboard.html', subscription_count=subscription_count,
                           web_site_users=web_site_users, distinct_discord_user_count=distinct_discord_user_count,
                           text_to_image_requests=text_to_image_requests, upscale_requets=upscale_requets,
                           text_to_video=text_to_video, image_to_video=image_to_video)


@admin_routes_bp.route('/text_to_image_requests_chart_data')
def get_text_to_image_chart_data():
    time_frame = request.args.get('timeFrame', 'daily')
    now = datetime.now()

    if time_frame == 'daily':
        start_date = now - timedelta(days=1)
        interval = 'hour'
    elif time_frame == 'weekly':
        start_date = now - timedelta(days=7)
        interval = 'day'
    elif time_frame == 'monthly':
        start_date = now - timedelta(days=30)
        interval = 'day'
    else:
        return jsonify({"error": "Invalid time frame"}), 400

    # Veritabanından 'consistent' alanına göre ayırarak veri çekiyoruz
    story_requests = TextToImage.objects(datetime__gte=start_date, consistent=True)
    image_generation_requests = TextToImage.objects(datetime__gte=start_date, consistent=False)

    # Verileri gruplamak
    story_data = {}
    image_generation_data = {}

    for req in story_requests:
        time_key = req.datetime.strftime('%Y-%m-%d %H' if interval == 'hour' else '%Y-%m-%d')
        story_data[time_key] = story_data.get(time_key, 0) + 1

    for req in image_generation_requests:
        time_key = req.datetime.strftime('%Y-%m-%d %H' if interval == 'hour' else '%Y-%m-%d')
        image_generation_data[time_key] = image_generation_data.get(time_key, 0) + 1

    labels = sorted(set(story_data.keys()).union(image_generation_data.keys()))

    story_counts = [story_data.get(label, 0) for label in labels]
    image_generation_counts = [image_generation_data.get(label, 0) for label in labels]

    return jsonify({
        "labels": labels,
        "storyData": story_counts,
        "imageGenerationData": image_generation_counts
    })


@admin_routes_bp.route('/upscale_requests_chart_data')
def get_upscale_chart_data():
    time_frame = request.args.get('timeFrame', 'daily')
    now = datetime.utcnow()

    if time_frame == 'daily':
        start_date = now - timedelta(days=1)
        interval = 'hour'
    elif time_frame == 'weekly':
        start_date = now - timedelta(days=7)
        interval = 'day'
    elif time_frame == 'monthly':
        start_date = now - timedelta(days=30)
        interval = 'day'
    else:
        return jsonify({"error": "Invalid time frame"}), 400

    # Tarih aralığına göre filtreleme
    requests = Upscale.objects(datetime__gte=start_date)

    # Veriyi istenen zaman dilimine göre grupla
    data = {}
    for req in requests:
        time_key = req.datetime.strftime('%Y-%m-%d %H' if interval == 'hour' else '%Y-%m-%d')
        data[time_key] = data.get(time_key, 0) + 1

    labels = sorted(data.keys())
    counts = [data[label] for label in labels]

    return jsonify({"labels": labels, "data": counts})






