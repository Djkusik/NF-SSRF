import argparse
from server import app, start_listener, db
from models import Target

targets = {}

def create_parser():
    parser = argparse.ArgumentParser(description='HTTP listener for SSRF fires.')
    parser.add_argument('-n', '--target-name', nargs='?', help='The name of the to be added target', default=None)
    parser.add_argument('-d', '--target-domain', nargs='?', help='The domain of the to be added target. It\'s optional, but becomes useful when a payload fires after a a weeks of delay.', default=None)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = create_parser()
    name = args.target_name
    domain = args.target_domain
    if name is not None:
        target = Target(name=name, domain=domain)
        db.session.add(target)
        db.session.commit()
    start_listener()
