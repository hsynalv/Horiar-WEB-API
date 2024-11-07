import logging

from flask import request
from flask_socketio import emit, join_room, rooms
from app import socketio


@socketio.on('connect')
def handle_connect():
    logging.error(f"Client connected: {request.sid}")
    emit('message', {'status': 'connected', 'message': 'Connection established'})


@socketio.on('join')
def handle_join(data):
    logging.error("join fonksiyonu tetiklendi.")
    room = data.get('room')
    logging.error(f"join fonksiyonunda gelen data: {data}")
    logging.error(f"gelen room = {room}")
    if room:
        logging.info(f"Joining room {room}")
        join_room(room)

        # Kullanıcının gerçekten katıldığını doğrulama
        emit('message', {'status': 'joined', 'room': room}, to=room)
    else:
        emit('message', {'status': 'error', 'message': 'Room ID is required to join'})


@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Client disconnected: {request.sid}")
