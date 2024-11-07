from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO(
    cors_allowed_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:3000",
        "https://horiar.com",
        "https://www.horiar.com"
    ],
    async_mode='eventlet',  # Yalnızca WebSocket bağlantısı için 'eventlet' seçin
    logger=True,
    engineio_logger=True  # Bağlantı detaylarını loglamak için
)


