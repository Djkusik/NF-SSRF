from flask import Flask, request
import logging, sys
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///listeners.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Target, Fire
db.create_all()

def disable_flask_logging():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

def disable_flask_banner():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None


def print_fire(name, domain, payload, headers):
    domain = domain if domain else 'Not specified'
    print(f'[*] Payload Fired on: {name}', f'Domain: {domain}', f'Payload: {payload}', f'Headers: {headers}', sep='\n\n[*] ')

@app.route("/<target_name>/<payload>")
def hello(target_name, payload):
    try:
        target = Target.query.filter_by(name=target_name).first()
        print_fire(target.name, target.domain, payload, request.headers)
    except KeyError:
        return 'Target name not found', 404
    return target.name

def start_listener(port='8888', address='127.0.0.1'):
    disable_flask_banner()
    disable_flask_logging()
    app.run(address, port)