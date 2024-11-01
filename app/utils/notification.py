from app import socketio

def notify_status_update(room, status, message):
    socketio.emit('message', {'status': status, 'message': message}, to=room)
