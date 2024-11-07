import logging

from flask import request
from flask_socketio import emit, join_room, rooms
from app import socketio

@socketio.on('connect')
def handle_connect():
    logging.info(f"Client connected: {request.sid}")
    emit('message', {'status': 'connected', 'message': 'Connection established'})


@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        # Katılımı loglamak
        logging.info(f"Kullanıcı room'a katıldı: {room}")

        # Kullanıcının room'a katılıp katılmadığını kontrol et
        if room in rooms(request.sid):
            logging.info(f"Room '{room}' başarılı şekilde katılındı.")
            emit('message', {'status': 'joined', 'room': room}, to=room)
        else:
            logging.warning(f"Kullanıcı room'a katılamadı: {room}")
    else:
        emit('message', {'status': 'error', 'message': 'Room ID is required to join'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
