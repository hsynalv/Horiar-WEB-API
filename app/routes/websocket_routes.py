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
    logging.info(f"join fonksiyonunda gelen data: {data}")
    logging.info(f"gelen room = {room}")
    if room:
        logging.info(f"Joining room {room}")
        join_room(room)

        # Kullanıcının gerçekten katıldığını doğrulayalım
        if room in rooms(request.sid):
            logging.info(f"Kullanıcı {room} odasına başarıyla katıldı.")
            emit('message', {'status': 'joined', 'room': room}, to=room)
        else:
            logging.warning(f"{room} odasına katılım başarısız.")
            emit('message', {'status': 'error', 'message': f'Could not join room {room}'})
    else:
        emit('message', {'status': 'error', 'message': 'Room ID is required to join'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
