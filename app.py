from app import create_app, socketio

# Uygulamayı başlatıyoruz
app = create_app()

# `socketio` nesnesini dışa aktararak `gunicorn` ile çalışmasını sağlıyoruz
