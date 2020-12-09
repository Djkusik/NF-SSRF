import os
import sys
sys.path.append('..')

from .payload_generator import PayloadGenerator
from common.logger import setup_logger, log_level


def web_run(target_domain, forgery_domain, list_path, list_name, log_path, protocols=['http','https','dict'], ports=['22', '80', '443']):
    if not os.path.isdir(log_path):
        os.mkdir(log_path)
    if not os.path.isdir(list_path):
        os.mkdir(list_path)

    setup_logger(log_level(3), f"{log_path}/ssrf_payloads.log")
    pg = PayloadGenerator(target_domain, forgery_domain, save_path=list_path, payload_filename=list_name, protocols=protocols, ports=ports)
    pg.run()