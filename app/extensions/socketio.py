from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://www.horiar.com", "https://horiar.com", "http://localhost:5000", "http://127.0.0.1:5500", "http://localhost:3000", "http://127.0.0.1:3000"], "supports_credentials": True}})

socketio = SocketIO(app, cors_allowed_origins=[
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
    "https://horiar.com",
    "https://www.horiar.com"
])

def notify_user_via_websocket(user_id, message):
    """
    Belirli bir kullanıcıya websocket üzerinden bildirim gönderir.

    :param user_id: Bildirimin gönderileceği kullanıcı kimliği
    :param message: Gönderilecek bildirim mesajı
    """
    socketio.emit('user_notification', {'user_id': user_id, 'message': message})
