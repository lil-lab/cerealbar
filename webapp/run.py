from webapp import socketio, app
import faulthandler
import eventlet
from webapp.threads import maintain_lobby

eventlet.monkey_patch()
eventlet.spawn(maintain_lobby)

if __name__ == '__main__':
    faulthandler.enable()

    socketio.run(app, host='0.0.0.0', port=8080)