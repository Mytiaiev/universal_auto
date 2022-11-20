import asyncio
import logging
import os
import re

from asgiref.sync import sync_to_async

from app.models import RawGPS
from auto.tasks import raw_gps_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

HOST, PORT = '0.0.0.0', 44300


class PackageHandler:
    pattern = r'#(.*?)#(.*?)\r\n'
    answer_login = '#AL#1\r\n'
    answer_bad_login = '#AL#0\r\n'
    answer_data = '#AD#1\r\n'
    answer_bad_data = '#AD#-1\r\n'
    answer_ping = '#AP#\r\n'

    def __init__(self):
        self.imei = ''

    async def _l_handler(self, **kwargs):
        imei = kwargs['msg'].split(';')[0]
        if imei:
            self.imei = imei
            return self.answer_login
        else:
            return self.answer_bad_login

    async def _d_handler(self, **kwargs):
        if len(self.imei) and len(kwargs['msg']):
            obj = await sync_to_async(RawGPS.objects.create)(imei=self.imei, client_ip=kwargs['addr'][0],
                                                       client_port=kwargs['addr'][1], data=kwargs['msg'])
            raw_gps_handler.delay(obj.id)
            return self.answer_data
        else:
            return self.answer_bad_data

    async def _p_handler(self, **kwargs):
        return self.answer_ping

    async def process_package(self, addr, message):
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
                res += await func(addr=addr, msg=item[1])
            if len(res):
                return res
            else:
                return self.answer_bad_data
        except Exception:
            return self.answer_bad_data


async def handle_connection(reader, writer):
    addr = writer.get_extra_info("peername")
    logging.info(msg=f"Connected by {addr}")
    ph = PackageHandler()
    while True:
        # Receive
        try:
            data = await reader.read(1024)
        except ConnectionError:
            logging.info(msg=f"Client suddenly closed while receiving from {addr}")
            break
        if not data:
            break
        answer = await ph.process_package(addr, data.decode('utf-8'))
        try:
            writer.write(answer.encode('utf-8'))
        except ConnectionError:
            logging.info(msg=f"Client suddenly closed, cannot send")
            break
    writer.close()
    logging.info(msg=f"Disconnected by {addr}")


async def main(host, port):
    server = await asyncio.start_server(handle_connection, host, port)
    async with server:
        await server.serve_forever()


def run():
    asyncio.run(main(HOST, PORT))
