from flask import Flask, request
import argparse
import logging
import sys

def disable_flask_logging():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

def disable_flask_banner():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None

app = Flask(__name__)

targets = {}

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    args = parser.parse_args()
    return args

class Target:
    def __init__(self, name, domain):
        # TODO exclude characters like /?#% from the name
        self.name = name
        self.domain = domain
    
def print_fire(name, domain, payload, headers):
    domain = domain if domain else 'Not specified'
    print(f'[*] Payload Fired on: {name}', f'Domain: {domain}', f'Payload: {payload}', f'Headers: {headers}', sep='\n\n[*] ')

@app.route("/<target_name>/<payload>")
def hello(target_name, payload):
    try:
        target = targets[target_name]
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
        target = Target(name, domain)
        targets[name] = target
    start_listener()
