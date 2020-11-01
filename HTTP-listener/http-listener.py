import argparse
from server import app, start_listener, db, print_fire
from models import Target, Fire

targets = {}

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    parser.add_argument('-sf', '--show-fires', nargs='?', const=25)
    args = parser.parse_args()
    return args

def show_fires(last=25):
    fires = Fire.query.limit(last).all()
    for fire in fires:
        print_fire(fire.target.name, fire.target.domain, fire.payload, fire.headers)



if __name__ == "__main__":
    args = create_parser()
    if args.show_fires:
        show_fires(args.show_fires)
    name = args.target_name
    domain = args.target_domain
    if name is not None:
        target = Target(name=name, domain=domain)
        db.session.add(target)
        db.session.commit()
    start_listener()
