from datetime import datetime, timedelta

from app.models.ip_request_log import IPRequestLog

MAX_REQUEST_LIMIT = 5  # Her IP için istek limiti

def track_ip_request(ip_address):
    # Veritabanında bu IP'yi arıyoruz
    log = IPRequestLog.objects(ip_address=ip_address).first()

    if not log:
        # Eğer bu IP ilk defa istek yapıyorsa, kaydı oluştur
        log = IPRequestLog(ip_address=ip_address, request_count=1)
        log.save()
        return True
    else:
        # Eğer son istek 24 saat önce yapıldıysa sayaç sıfırlanır
        if datetime.utcnow() - log.last_request_time > timedelta(days=1):
            log.request_count = 0

        # İstek limitini kontrol ediyoruz
        if log.request_count >= MAX_REQUEST_LIMIT:
            return False

        # Eğer limit aşılmamışsa, sayaç güncellenir
        log.increment_request()
        return True
