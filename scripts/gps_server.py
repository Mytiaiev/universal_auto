import logging
import os
from socket import * 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
UDP_IP = os.environ['UDP_IP']
UDP_PORT = 44300

def run():
    sockfd = socket(AF_INET, SOCK_STREAM)
    sockfd.bind(("0.0.0.0", UDP_PORT))
    logging.info(msg="Hello TCP THREAD on Fly.io!")
    sockfd.listen() 
    while True:
        newsockfd, address = sockfd.accept() 
        data = newsockfd.recv(1024)
        logging.info(msg=data)
        
        message = "TCP OK".encode()
        logging.info(msg=message)
        
        newsockfd.send(message)
        newsockfd.close()
    