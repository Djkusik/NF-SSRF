import argparse
from server import app, start_listener, db, print_fire
from models import Target, Fire
from sqlalchemy import exc

targets = {}

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    parser.add_argument('-sf', '--show-fires', nargs='?', const=25)
    parser.add_argument('-st', '--show-targets', nargs='?', const=25)
    args = parser.parse_args()
    return args

def show_fires(last=25):
    fires = Fire.query.limit(last).all()
    print('[*][*] Fires')
    for fire in fires:
        print_fire(fire.target.name, fire.target.domain, fire.payload, fire.headers)

def show_targets(last=25):
    targets = Target.query.limit(last).all()
    print('[*][*] Targets')
    for target in targets:
        fires = len(Fire.query.filter_by(target=target).all())
        print(f'[*] Target name: {target.name}\n[*] Target domain: {target.domain}\n[*] Fires: {fires}')



if __name__ == "__main__":
    args = create_parser()
    name = args.target_name
    domain = args.target_domain

    if name is not None:
        target = Target(name=name, domain=domain)
        try:
            db.session.add(target)
            db.session.commit()
        except exc.IntegrityError:
            # name must be unique
            db.session.rollback()
            print(f'[*] target with name {name} is already present')

    
    if args.show_fires:
        show_fires(args.show_fires)
    if args.show_targets:
        show_targets(args.show_targets)
    start_listener()
