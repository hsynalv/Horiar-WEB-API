from app import socketio

def notify_status_update(room, status, message):
    socketio.emit('message', {'status': status, 'message': message}, to=room)


def notify_user_via_websocket(user_id, message):
    """
    Belirli bir kullanıcıya websocket üzerinden bildirim gönderir.

    :param user_id: Bildirimin gönderileceği kullanıcı kimliği
    :param message: Gönderilecek bildirim mesajı
    """
    socketio.emit('message', {'user_id': user_id, 'message': message})
