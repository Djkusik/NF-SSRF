import socket
import pathlib
import binascii
import os

from functools import reduce
from operator import add
from datetime import datetime
from common.logger import get_logger
from payload_generator.register import Register


class PayloadGenerator:

    register = Register()

    def __init__(self, target_addr, forgery_addr, save_path='./payloads', payload_filename=None):
        self.target_addr = target_addr
        self.forgery_addr = forgery_addr
        self.ip_formats_path = str(pathlib.Path(__file__).parent.absolute()) + '/ip_formats.txt'
        self.save_path = save_path
        self.payload_filename = payload_filename

        try:
            self.forgery_ip = self.get_ip_from_addr(self.forgery_addr)
        except socket.gaierror:
            self.logger.warning('Wrong forgery address format or DNS problem')
            self.forgery_ip = None

        if not os.path.isdir(self.save_path):
            os.mkdir(self.save_path)

        # self.logger = get_logger()

    def get_ip_from_addr(self, hostname):
        return socket.gethostbyname(hostname)

    def get_addr_from_ip(self, ip):
        return socket.gethostbyaddr(ip)[0]

    def create_every_ip_format(self):
        forgery_formats = [self.forgery_addr, self.forgery_ip]

        for func in self.register:
            forgery_formats += func(self, self.forgery_ip)
        forgery_formats += [self.add_protocol(protocol, addr) for addr in forgery_formats for protocol in ['http', 'https']]

        return forgery_formats

    def add_protocol(self, protocol, addr):
        return protocol + '://' + addr

    @register
    def ip_to_int(self, ip):
        return [str(reduce(add, [ int(octet) * (256 ** i) for i, octet in enumerate(reversed(ip.split('.'))) ]))]

    @register
    def ip_to_octal(self, ip):
        return ['%04o.%04o.%04o.%04o' % tuple(map(int, ip.split('.')))]

    @register
    def ip_to_hex(self, ip):
        return ['0x' + binascii.hexlify(socket.inet_aton(ip)).decode('utf-8')]

    @register
    def create_formats_from_file(self, ip):
        with open(self.ip_formats_path, 'r') as f:
            formats = f.read().splitlines()
        
        created_formats = []
        for octet_format in formats:
            types = octet_format.split(',')
            created_formats.append(self.create_mixed_ip(self.forgery_ip, types))
        return created_formats
        
    def create_mixed_ip(self, ip, octet_types):
        return (
            f'{self.octet_to_format(ip, 1, octet_types[0])}.'
            f'{self.octet_to_format(ip, 2, octet_types[1])}.'
            f'{self.octet_to_format(ip, 3, octet_types[2])}.'
            f'{self.octet_to_format(ip, 4, octet_types[3])}'
        )

    def octet_to_format(self, ip, octet, octet_format):
        return {
            'int': self.octet_to_int,
            'oct': self.octet_to_octal,
            'hex': self.octet_to_hex,
            'dot': self.octet_to_dot
        }[octet_format](ip, octet)

    def octet_to_int(self, ip, octet):
        return str((int(ip.split('.')[octet - 1]) * (256 ** abs(octet - 4))))

    def octet_to_octal(self, ip, octet):
        return '%04o' % int(ip.split('.')[octet - 1])

    def octet_to_hex(self, ip, octet):
        return hex(int(ip.split('.')[octet - 1]))

    def octet_to_dot(self, ip, octet):
        return ip.split('.')[octet - 1]

    def save_to_file(self, payloads):
        full_path = self.get_fullpath()
        with open(full_path, 'w+') as f:
            for payload in payloads:
                f.write(payload + '\n')

    def get_fullpath(self):
        now = datetime.now()
        today_folder = self.get_today_folder(now)

        if self.payload_filename is not None:
            return f"{today_folder}/{self.payload_filename}"
        else:
            return f"{today_folder}/{now.strftime('%H%M%S_payloads.txt')}"

    def get_today_folder(self, now):
        today_folder = f"{self.save_path}/{now.strftime('%Y%m%d')}"
        if not os.path.isdir(today_folder):
            os.mkdir(today_folder)
        return today_folder

    def run(self):
        forgery_formats = self.create_every_ip_format()
        self.save_to_file(forgery_formats)


