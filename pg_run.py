import sys
import validators
import argparse

from payload_generator.payload_generator import PayloadGenerator
from common.logger import setup_logger, log_level


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('tdomain', help='Target domain', type=str)
    parser.add_argument('ldomain', help='Listening domain', type=str)
    parser.add_argument('-p', '--ports', help="List of ports used to generate payloads", nargs="+", default=['22', '80', '443'])
    parser.add_argument('-pr', '--protocols', help='List of protocols used to generate payloads', nargs="+", default=['http','https','dict'])
    args = parser.parse_args()
    if not validators.domain(args.tdomain) and not validators.ip_address.ipv4(args.tdomain):
        print("Target domain is not a proper domain name")
        sys.exit(1)
    target_domain = args.tdomain

    if not validators.domain(args.ldomain) and not validators.ip_address.ipv4(args.ldomain):
        print("Listening domain is not a proper domain name")
        sys.exit(1)
    forgery_domain = args.ldomain
    ports = args.ports
    protocols = args.protocols

    return target_domain, forgery_domain, ports, protocols


if __name__ == '__main__':
    target_domain, forgery_domain, ports, protocols = parse_args()
    setup_logger(log_level(3))
    pg = PayloadGenerator(target_domain, forgery_domain, ports=ports, protocols=protocols)
    pg.run()