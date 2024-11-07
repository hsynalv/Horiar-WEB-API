import logging

from flask import request
from flask_socketio import emit, join_room
from app import socketio

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('message', {'status': 'connected', 'message': 'Connection established'})


@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    logging.info(f"Received join request with data: {data}")
    logging.info(f"room = {room}")
    if room:
        logging.info(f"Joining room {room}")
        join_room(room)
        emit('message', {'status': 'joined', 'room': room}, to=room)
    else:
        emit('message', {'status': 'error', 'message': 'Room ID is required to join'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
