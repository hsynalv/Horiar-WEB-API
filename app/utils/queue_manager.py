import logging

import redis
from rq import Queue
from app.utils.notification import notify_status_update

# Redis bağlantısı için 'redis-server' host ismini kullanıyoruz
redis_conn = redis.Redis(host='redis-server', port=6380, db=0)

# Farklı iş türleri için ayrı kuyruklar tanımlıyoruz
image_generation_queue = Queue('image_generation', connection=redis_conn)
video_generation_queue = Queue('video_generation', connection=redis_conn)
upscale_queue = Queue('upscale', connection=redis_conn)

def add_to_queue(queue, func, *args, **kwargs):
    """Genel kuyruk fonksiyonu. Verilen kuyrukta işlemi başlatır ve istemciye durum güncellemesi gönderir."""
    # 1 gün boyunca saklanmasını sağlamak için result_ttl parametresi ekleniyor
    job = queue.enqueue(func, *args, result_ttl=86400, **kwargs)
    notify_status_update(kwargs.get('room'), 'queued', 'Your request is in the queue.')
    return job

def add_to_image_queue(func, *args, **kwargs):
    """Fonksiyonu image_generation kuyruğunda çalıştırır."""
    return add_to_queue(image_generation_queue, func, *args, **kwargs)

def add_to_upscale_queue(func, *args, **kwargs):
    """Fonksiyonu upscale kuyruğunda çalıştırır."""
    return add_to_queue(upscale_queue, func, *args, **kwargs)

def add_to_video_queue(func, *args, **kwargs):
    """Fonksiyonu video kuyruğunda çalıştırır."""
    return add_to_queue(video_generation_queue, func, *args, **kwargs)
