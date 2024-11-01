from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins=["http://localhost", "http://127.0.0.1","http://127.0.0.1:5500", "https://horiar.com", "https://www.horiar.com"])


def notify_user_via_websocket(user_id, message):
    """
    Belirli bir kullanıcıya websocket üzerinden bildirim gönderir.

    :param user_id: Bildirimin gönderileceği kullanıcı kimliği
    :param message: Gönderilecek bildirim mesajı
    """
    # WebSocket bağlantısı ile kullanıcıya mesaj gönderiyoruz
    socketio.emit('user_notification', {'user_id': user_id, 'message': message})
