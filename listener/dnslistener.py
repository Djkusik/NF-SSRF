#!/usr/bin/env python3
# coding=utf-8
"""
LICENSE http://www.apache.org/licenses/LICENSE-2.0
"""
import argparse
import datetime
import sys
import time
import threading
import traceback
import socketserver
import struct
from random import randrange
try:
    from dnslib import *
except ImportError:
    print("Missing dependency dnslib: <https://pypi.python.org/pypi/dnslib>. Please install it with `pip`.")
    sys.exit(2)

from models import Fire, Target
from db import db

# a global domain object, that will be initialized with values later
D = None

class Domain():

    def __init__(self, domain, ip_address, TTL=0):
        # the actual DNS queries have the . at the end
        self.domain = domain + '.'
        self.ip_address = ip_address
        self.TTL = TTL
        self.counter = 0


    # this functions returns one of the IP addresses
    def get_records(self):
        records = {
           self.domain: [A(self.ip_address), ],
        }
        return records

    def __str__(self):
        return self.domain


def print_fire(date, name, domain, fire_type, payload):
    domain = domain if domain else 'Not specified'
    print(f'[*] Payload Fired on: {name}', f'Date: {date}', f'Domain: {domain}', f'Type: {fire_type}', f'Payload: {payload}', sep='\n[*] ')


def register_fire(target_name, payload):
    target = Target.query.filter_by(name=target_name).first()
    if target is None:
        return None
        # return 'Target name not found', 404
    fire = Fire(payload=payload, target=target, dns_fire=True)
    db.session.add(fire)
    db.session.commit()
    print_fire(fire.date.strftime("%Y-%m-%d %H:%M"), target.name, target.domain, 'DNS', payload)


def dns_response(data):
    request = DNSRecord.parse(data)

    reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)

    qname = request.q.qname
    qn = str(qname)
    qtype = request.q.qtype
    qt = QTYPE[qtype]


    # does the query apply to our domain?
    if qn.endswith('.' + str(D)):
        payload_end = qn.rfind(str(D))
        payload = qn[:payload_end - 1]
        if '.' in payload:
            target = payload.split('.')[-1]
            payload = '.'.join(payload.split('.')[:-1])
            register_fire(target, payload)
        else:
            print(payload)


        # get the record with the IP address, different on each query
        records = D.get_records()

        # this for is in case we have more than one domain 
        for name, rrs in records.items():

            # does this record apply to the queried domain?
            if name == qn:
                # one record may contain more data to response eg. AAAA records
                for rdata in rrs:
                    rqt = rdata.__class__.__name__
                    if qt in ['*', rqt]:

                        reply.add_answer(RR(rname=qname, rtype=getattr(QTYPE, rqt), rclass=1, ttl=D.TTL, rdata=rdata))



    return reply.pack()


class BaseRequestHandler(socketserver.BaseRequestHandler):

    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        # print("\n\n%s request %s (%s %s):" % (self.__class__.__name__[:3], now, self.client_address[0],
        #                                       self.client_address[1]))
        try:
            data = self.get_data()
            self.send_data(dns_response(data))
        except Exception:
            traceback.print_exc(file=sys.stderr)


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0].strip()

    def send_data(self, data):
        return self.request[1].sendto(data, self.client_address)


def create_parser():
    parser = argparse.ArgumentParser(description='Start a DNS server for DNS rebinding attacks implemented in Python.')
    parser.add_argument('-p', '--port', default=53, type=int, help='The port to listen on. 53 is the default value.')
    parser.add_argument('-d', '--domain', required=True, help='The domain for which the DNS queries will be sent. It has to be a subdomain of a domain whose nameservers point to this machine.')
    parser.add_argument('-i', '--ip', required=False, nargs='+', default='127.0.0.1', help='IP addresses that will be in the response to the A DNS queries for the domain specified in --domain parameter. If not provided, 127.0.0.1 will be returned')
    parser.add_argument('--ttl', default=0, nargs='?', help='TTL of the DNS responses. 0 is the default value.')
    args = parser.parse_args()
    return args


def start_server(domain, ip_address='127.0.0.1', ttl=0, port=53):
    print("Starting nameserver...")
    global D
    D = Domain(domain, ip_address, ttl)
    
    server = socketserver.ThreadingUDPServer(('', port), UDPRequestHandler)

    thread = threading.Thread(target=server.serve_forever)  # that thread will start one more thread for each request
    thread.daemon = True  # exit the server thread when the main thread terminates
    thread.start()
    print("%s server loop running in thread: %s" % (server.RequestHandlerClass.__name__[:3], thread.name))

    return server, thread


def main():
    args = create_parser()
    server, thread = start_server(args.domain, args.ip, args.ttl, args.port)
    
    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()

if __name__ == '__main__':
    main()

