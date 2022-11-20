import logging
import os
import re

from app.models import RawGPS

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

from socket import * 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
# UDP_IP = os.environ['UDP_IP']
# UDP_PORT = 44300
TCP_IP = os.environ['UDP_IP']
TCP_PORT = 44300


class PackageHandler:
    pattern = r'#(.*?)#(.*?)\r\n'
    answer_login = '#AL#1\r\n'
    answer_bad_login = '#AL#0\r\n'
    answer_data = '#AD#1\r\n'
    answer_bad_data = '#AD#-1\r\n'
    answer_ping = '#AP#\r\n'

    def __init__(self):
        self.imei = ''

    def _l_handler(self, **kwargs):
        imei = kwargs['msg'].split(';')[0]
        if imei:
            self.imei = imei
            return self.answer_login
        else:
            return self.answer_bad_login

    def _d_handler(self, **kwargs):
        if len(self.imei) and len(kwargs['msg']):
            obj = RawGPS.objects.create(imei=self.imei, client_ip=kwargs['addr'][0],
                                  client_port=kwargs['addr'][1], data=kwargs['msg'])
            # logging.info(msg=f"Added [{kwargs['addr']}] {self.imei} {kwargs['msg']}")
            return self.answer_data
        else:
            return self.answer_bad_data

    def _p_handler(self, **kwargs):
        return self.answer_ping

    def process_package(self, addr, message):
        try:
            message_ = re.sub(r'\r\n', '', message)
            logging.info(msg=f"Received from {addr}: {message_}")
            handlers = {
                'L': self._l_handler,
                'D': self._d_handler,
                'P': self._p_handler,
            }
            res = ''
            match = re.findall(self.pattern, message)
            for item in match:
                func = handlers[item[0]]
                res += func(addr=addr, msg=item[1])
            if len(res):
                return res
            else:
                return self.answer_bad_data
        except Exception:
            return self.answer_bad_data




def run():
    with socket(AF_INET, SOCK_STREAM) as serv_sock:
        serv_sock.bind((TCP_IP, TCP_PORT))
        serv_sock.listen()
        while True:
            logging.info(msg=f"Waiting for connection...")
            sock, addr = serv_sock.accept()
            with sock:
                logging.info(msg=f"Connected by {addr}")
                ph = PackageHandler()
                while True:
                    try:
                        data = sock.recv(1024)
                    except ConnectionError:
                        logging.info(msg=f"Client suddenly closed while receiving")
                        break
                    answer = ph.process_package(addr, data.decode('utf-8'))
                    try:
                        sock.sendall(answer.encode('utf-8'))
                    except ConnectionError:
                        logging.info(msg=f"Client suddenly closed, cannot send")
                        break
                logging.info(msg=f"Disconnected by {addr}")