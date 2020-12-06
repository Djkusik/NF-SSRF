from flask import Flask, request
import logging, sys
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

def disable_flask_logging():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

def disable_flask_banner():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None


def print_fire(date, name, domain, fire_type, payload, headers):
    domain = domain if domain else 'Not specified'
    print(f'[*] Payload Fired on: {name}', f'Date: {date}', f'Domain: {domain}', f'Type: {fire_type}', f'Payload: {payload}', f'Headers: {headers}', sep='\n[*] ', end='\n\n')

@app.route("/<target_name>/<payload>")
def hello(target_name, payload):
    from models import Target, Fire
    from db import db
    target = Target.query.filter_by(name=target_name).first()
    if target is None:
        return page_not_found(None)
        # return 'Target name not found', 404
    fire = Fire(payload=payload, headers=str(request.headers), target=target, dns_fire=False)
    db.session.add(fire)
    db.session.commit()
    print_fire(fire.date.strftime("%Y-%m-%d %H:%M"), target.name, target.domain, 'HTTP', payload, request.headers)
    return target.name

@app.errorhandler(404)
def page_not_found(e):
    print(f'[*] Unknown request.\n[*] Path: {request.path}\n[*] Headers: {request.headers}')
    return 'Unknown address', 404

def start_listener(port='8888', address='127.0.0.1'):
    disable_flask_banner()
    disable_flask_logging()
    app.run(address, port)