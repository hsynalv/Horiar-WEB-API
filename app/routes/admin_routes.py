import logging
from datetime import datetime, timedelta

from bson import ObjectId
from flask import render_template, redirect, url_for, flash, Blueprint, session, request, jsonify
from flask_login import login_user, logout_user
from mongoengine import Q

from app.models.coupon_model import Coupon
from app.models.discord_image_request_model import DiscordImageRequest
from app.models.galley_photo_model import GalleryPhoto
from app.models.image_to_video_model import ImageToVideo
from app.models.package_model import Package
from app.models.purchase_model import Purchase
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


@admin_routes_bp.route('/image-requests', methods=['GET'])
def list_image_requests():
    if 'page' not in request.args:
        return render_template('admin/image_requests.html')

    try:
        # Sayfa ve limit parametrelerini al
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_order = request.args.get('sort_order', 'desc')  # Default olarak artan sıralama

        # Toplam öğe sayısını al
        total_items = TextToImage.objects.count()

        # Sıralama parametresine göre sıralama yap
        sort_field = 'datetime'
        if sort_order == 'desc':
            sort_field = '-datetime'

        # Veritabanından verileri getir
        image_requests = TextToImage.objects.order_by(sort_field).skip((page - 1) * limit).limit(limit)

        # Toplam sayfa sayısını hesapla
        total_pages = (total_items + limit - 1) // limit

        # JSON formatına dönüştür
        requests_list = [
            {
                "username": req.username,
                "datetime": req.datetime.strftime('%Y/%m/%d %H:%M'),
                "prompt": req.prompt,
                "prompt_fix": req.prompt_fix,
                "consistent": req.consistent,
                "image_url_webp": req.image_url_webp,
            }
            for req in image_requests
        ]

        return jsonify({
            "items": requests_list,
            "total_pages": total_pages,
            "current_page": page,
        }), 200
    except Exception as e:
        logging.error(f"Error fetching image requests: {e}")
        return jsonify({"error": str(e)}), 500


@admin_routes_bp.route('/text-to-video-requests', methods=['GET'])
def list_text_to_video_requests():
    if 'page' not in request.args:
        return render_template('admin/list_request/text_to_video_requests.html')

    try:
        # Parametreleri al
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_order = request.args.get('sort_order', 'desc')  # Varsayılan sıralama artan (asc)

        # Sıralama düzeni ayarla
        sort_criteria = '+datetime' if sort_order == 'asc' else '-datetime'

        # Veritabanı sorgusu
        total_items = TextToVideoGeneration.objects.count()
        video_requests = TextToVideoGeneration.objects.order_by(sort_criteria).skip((page - 1) * limit).limit(limit)

        # Sayfa sayısını hesapla
        total_pages = (total_items + limit - 1) // limit

        # JSON formatına dönüştür
        requests_list = [
            {
                "username": req.username,
                "datetime": req.datetime.strftime('%Y/%m/%d %H:%M'),
                "prompt": req.prompt,
                "video_url": req.video_url
            }
            for req in video_requests
        ]

        return jsonify({
            "items": requests_list,
            "total_pages": total_pages,
            "current_page": page
        }), 200
    except Exception as e:
        logging.error(f"Error fetching text-to-video requests: {e}")
        return jsonify({"error": str(e)}), 500


@admin_routes_bp.route('/image-to-video-requests', methods=['GET'])
def list_image_to_video_requests():
    if 'page' not in request.args:
        return render_template('admin/list_request/image_to_video_requests.html')

    try:
        # Parametreleri al
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_order = request.args.get('sort_order', 'desc')  # Varsayılan sıralama artan (asc)

        # Sıralama düzeni ayarla
        sort_criteria = '+datetime' if sort_order == 'asc' else '-datetime'

        # Veritabanı sorgusu
        total_items = ImageToVideo.objects.count()
        video_requests = ImageToVideo.objects.order_by(sort_criteria).skip((page - 1) * limit).limit(limit)

        # Sayfa sayısını hesapla
        total_pages = (total_items + limit - 1) // limit

        # JSON formatına dönüştür
        requests_list = [
            {
                "username": req.username,
                "datetime": req.datetime.strftime('%Y/%m/%d %H:%M'),
                "prompt": req.prompt,
                "image_url": req.image_url,
                "video_url": req.video_url
            }
            for req in video_requests
        ]

        return jsonify({
            "items": requests_list,
            "total_pages": total_pages,
            "current_page": page
        }), 200
    except Exception as e:
        logging.error(f"Error fetching image-to-video requests: {e}")
        return jsonify({"error": str(e)}), 500

@admin_routes_bp.route('/upscale-requests')
def list_upscale_requests():
    # Veritabanından tüm ImageRequest nesnelerini çekiyoruz
    requests = Upscale.objects()
    return render_template('admin/upscale_requests.html', image_requests=requests)


@admin_routes_bp.route('/discord-requests', methods=['GET'])
def discord_requests():
    try:

        if 'page' not in request.args:
            return render_template('admin/discord_requests.html')

        # Sayfa ve limit parametrelerini al
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))  # Varsayılan olarak 10 öğe

        # Toplam öğe sayısını al
        total_items = DiscordImageRequest.objects.count()

        # Sayfalama için veritabanından öğeleri al
        discord_requests = DiscordImageRequest.objects.skip((page - 1) * limit).limit(limit)

        # Toplam sayfa sayısını hesapla
        total_pages = (total_items + limit - 1) // limit

        # JSON formatına dönüştür
        requests_list = [
            {
                "username": req.username,
                "prompt": req.prompt,
                "guild": req.guild,
                "channel": req.channel,
                "datetime": req.datetime.strftime('%Y-%m-%d %H:%M'),
                "resolution": req.resolution,
                "model_type": req.model_type,
                "re_request": req.re_request,
            }
            for req in discord_requests
        ]

        return jsonify({
            "items": requests_list,
            "total_pages": total_pages,
            "current_page": page
        }), 200
    except Exception as e:
        logging.error(f"Error fetching discord requests: {e}")
        return jsonify({"error": str(e)}), 500

@admin_routes_bp.route('/subscriptions')
def list_subscription():
    requests = Subscription.objects()
    return render_template('admin/subscription/subscription.html', subscription_requests=requests)

@admin_routes_bp.route('/purchases')
def list_purchase():
    requests = Purchase.objects()
    return render_template('admin/purchase.html', purchases=requests)


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

        subs = Subscription.objects(user_id=user_id).first()
        if subs:
            subs.credit_balance += float(credit)
            subs.max_credit_balance += int(credit)
            subs.subscription_date = datetime.utcnow()
            subs.subscription_end_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            subs.merchant_oid = "HORIAR-KREDI-TANIMLAMA"

            subs.save()

            return jsonify({"success": True, "message": "Kredi eklemesi başarıyla tanımlandı!"}), 200

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

@admin_routes_bp.route('/text_to_video_requests_chart_data')
def get_text_to_video_chart_data():
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
    image_to_video_requests = ImageToVideo.objects(datetime__gte=start_date)
    video_generation_requests = TextToVideoGeneration.objects(datetime__gte=start_date)

    # Verileri gruplamak
    image_to_video_data = {}
    video_generation_data = {}

    for req in image_to_video_requests:
        time_key = req.datetime.strftime('%Y-%m-%d %H' if interval == 'hour' else '%Y-%m-%d')
        image_to_video_data[time_key] = image_to_video_data.get(time_key, 0) + 1

    for req in video_generation_requests:
        time_key = req.datetime.strftime('%Y-%m-%d %H' if interval == 'hour' else '%Y-%m-%d')
        video_generation_data[time_key] = video_generation_data.get(time_key, 0) + 1

    labels = sorted(set(image_to_video_data.keys()).union(video_generation_data.keys()))

    image_to_video_counts = [image_to_video_data.get(label, 0) for label in labels]
    video_generation_counts = [video_generation_data.get(label, 0) for label in labels]

    return jsonify({
        "labels": labels,
        "imageToVideoData": image_to_video_counts,
        "videoGenerationData": video_generation_counts
    })


# Dynamic Galery -------------------------------------------------------------------------------------------------

# Kullanıcı tarafından oluşturulmuş TextToImage görsellerini listeleme rotası
@admin_routes_bp.route('/user-images', methods=['GET'])
def list_user_images():
    try:
        # Eğer sadece sayfayı yüklemek istiyorsak (sayfa GET isteği ile geliyorsa)
        if 'page' not in request.args:
            return render_template('admin/gallery/user_images.html')

        # Eğer verileri JSON olarak almak istiyorsak (JavaScript ile API isteği)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))  # Varsayılan olarak 30 görsel gösteriyoruz
        query = request.args.get('query', '').strip()

        # TextToImage koleksiyonundan verileri sayfalama ile alıyoruz
        if query:
            user_images = TextToImage.objects.filter(
                Q(username__icontains=query)
            ).skip((page - 1) * limit).limit(limit)
            total_items = TextToImage.objects.filter(
                Q(username__icontains=query)
            ).count()
        else:
            user_images = TextToImage.objects.skip((page - 1) * limit).limit(limit)
            total_items = TextToImage.objects.count()

        # JSON formatına dönüştürme
        user_images_list = [image.to_dict() for image in user_images]
        total_pages = (total_items + limit - 1) // limit

        return jsonify({"images": user_images_list, "total_pages": total_pages, "total_items": total_items}), 200

    except Exception as e:
        logging.error(f"Error listing user images: {e}")
        return jsonify({"error": str(e)}), 500

# Kullanıcı tarafından oluşturulmuş bir TextToImage görselini galeriye ekleme rotası
@admin_routes_bp.route('/user-images/add-to-gallery', methods=['POST'])
def add_user_image_to_gallery():
    try:
        image_id = request.form.get('image_id')

        # Görselin varlığını kontrol et
        user_image = TextToImage.objects(id=image_id).first()
        if not user_image:
            return jsonify({"error": "Görsel bulunamadı"}), 404

        # Görseli GalleryPhoto olarak ekle
        gallery_photo = GalleryPhoto(
            title=user_image.prompt,  # Başlık olarak prompt kullanıyoruz
            description="Kullanıcı tarafından oluşturulmuş text to image görseli",
            prompt=user_image.prompt,
            image_url_webp=user_image.image_url_webp,  # Görsel verisini alıyoruz
            created_at=datetime.now(),
            image_url=user_image.image_url,
            user_id=str(user_image.id),
            is_visible=True,
            model_type=user_image.model_type,
            prompt_fix=user_image.prompt_fix,
            resolution=user_image.resolution,
            username=user_image.username
        )
        gallery_photo.save()

        """
            model_type = StringField()
        prompt_fix = StringField()
        resolution = StringField()
    """

        return jsonify({"message": "Görsel galeriye başarıyla eklendi"}), 201

    except Exception as e:
        logging.error(f"Error adding user image to gallery: {e}")
        return jsonify({"error": str(e)}), 500

# Fotoğrafları Listeleme Rotası
@admin_routes_bp.route('/gallery', methods=['GET'])
def list_gallery_photos():
    try:
        # Eğer sadece sayfayı yüklemek istiyorsak (sayfa GET isteği ile geliyorsa)
        if 'page' not in request.args:
            return render_template('admin/gallery/edit_gallery.html')

        # Eğer verileri JSON olarak almak istiyorsak (JavaScript ile API isteği)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))  # Varsayılan olarak 10 görsel gösteriyoruz

        # Sayfalama ile veritabanından fotoğrafları alıyoruz
        photos = GalleryPhoto.objects.skip((page - 1) * limit).limit(limit)
        total_items = GalleryPhoto.objects.count()  # Toplam öğe sayısını alıyoruz

        # JSON formatına dönüştürme
        photos_list = [photo.to_dict() for photo in photos]
        total_pages = (total_items + limit - 1) // limit  # Toplam sayfa sayısını hesaplıyoruz

        return jsonify({
            "photos": photos_list,  # Anahtar adı "photos" olmalı
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page
        }), 200

    except Exception as e:
        logging.error(f"Error listing gallery photos: {e}")
        return jsonify({"error": str(e)}), 500


# Fotoğraf Düzenleme Rotası
@admin_routes_bp.route('/gallery/<photo_id>', methods=['PUT'])
def update_gallery_photo(photo_id):
    try:
        # JSON verisini al
        data = request.get_json()

        # Fotoğrafı bul
        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        # Güncellemeler
        photo.title = data.get('title', photo.title)
        photo.description = data.get('description', photo.description)
        photo.tags = data.get('tags', photo.tags)  # Tags alanı da güncellenebilir.
        photo.is_visible = data.get('is_visible', photo.is_visible)

        photo.save()
        return jsonify({"message": "Fotoğraf başarıyla güncellendi"}), 200

    except Exception as e:
        logging.error(f"Error updating gallery photo: {e}")
        return jsonify({"error": str(e)}), 500

# Fotoğraf Silme Rotası
@admin_routes_bp.route('/gallery/<photo_id>', methods=['DELETE'])
def delete_gallery_photo(photo_id):
    try:
        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        photo.delete()
        return jsonify({"message": "Fotoğraf başarıyla silindi"}), 200

    except Exception as e:
        logging.error(f"Error deleting gallery photo: {e}")
        return jsonify({"error": str(e)}), 500

@admin_routes_bp.route('/gallery/<photo_id>', methods=['GET'])
def get_gallery_photo(photo_id):
    try:
        # Veritabanından ilgili fotoğrafı alıyoruz
        photo = GalleryPhoto.objects(id=photo_id).first()
        if not photo:
            return jsonify({"error": "Fotoğraf bulunamadı"}), 404

        # Fotoğrafın JSON formatına dönüştürülmüş hali
        return jsonify(photo.to_dict()), 200

    except Exception as e:
        logging.error(f"Error fetching gallery photo: {e}")
        return jsonify({"error": str(e)}), 500






