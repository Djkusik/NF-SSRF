from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import argparse
import logging
import sys
from datetime import datetime

def disable_flask_logging():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

def disable_flask_banner():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///listeners.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
targets = {}

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    args = parser.parse_args()
    return args

# class Target:
#     def __init__(self, name, domain):
#         # TODO exclude characters like /?#% from the name
#         self.name = name
#         self.domain = domain
class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    domain = db.Column(db.String(80), nullable=True)

    def __repr__(self):
        return self.name

class Fire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payload = db.Column(db.String(255), nullable=False)
    date = db.Column()
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    target = db.relationship('Target', backref=db.backref('targets', lazy=True))

db.create_all()
    
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

        
    

if __name__ == "__main__":
    args = create_parser()
    name = args.target_name
    domain = args.target_domain
    if name is not None:
        target = Target(name=name, domain=domain)
        db.session.add(target)
        db.session.commit()
    start_listener()
