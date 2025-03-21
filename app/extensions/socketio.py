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
        "https://www.horiar.com",
        "https://horiar-client-git-development-mostafa-horiar.vercel.app"
    ],
    async_mode='eventlet',  # Yalnızca WebSocket bağlantısı için 'eventlet' seçin
    logger=False,
    engineio_logger=False  # Bağlantı detaylarını loglamak için
)


