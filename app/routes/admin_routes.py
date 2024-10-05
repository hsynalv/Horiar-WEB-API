from flask import render_template, redirect, url_for, flash, Blueprint, session
from flask_login import login_user, logout_user
from app.models.user_model import User
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
