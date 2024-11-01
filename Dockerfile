# Python imajını kullanıyoruz (örneğin, Python 3.10)
FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Gereksinimleri yükle
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Flask-SocketIO, RQ, Redis, RQ-Dashboard ve Gunicorn kurulumları
RUN pip install eventlet rq redis rq-dashboard gunicorn

# Uygulama dosyalarını kopyala
COPY . .

# Ortam değişkenlerini ayarla
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Portları expose et (Flask 5000, RQ-Dashboard 9181)
EXPOSE 5000 9181

# CMD komutu ile ana uygulama komutunu tanımla (app konteyneri için geçerli olacak)
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:create_app()"]
