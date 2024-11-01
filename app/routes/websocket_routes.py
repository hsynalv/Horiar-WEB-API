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
    join_room(room)
    emit('message', {'status': 'joined', 'room': room}, to=room)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
