from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)

app.config['DEBUG'] = False
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Packages and modules
from webapp.game_manager import start, disconn
from webapp import events

# Blueprints
from webapp.routes.home import home
from webapp.routes.other import blank

app.register_blueprint(home)
app.register_blueprint(blank)


# Control caching
@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    return response
