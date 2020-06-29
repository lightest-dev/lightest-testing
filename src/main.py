import json
import os.path
import logging
import socket
from concurrent import futures
import grpc
from command_provider import CommandProvider
from grpc_server import GrpcServer
from models.limits import Limits
from protos import CodeTester_pb2_grpc
from sender import Sender
from checker import CodeChecker
from models import Settings
import protos.CodeTester_pb2_grpc


def add_ports(server):
    adress = '[::]:10000'
    key_path = './server.key'
    if os.path.isfile(key_path):
        logging.info('Seeting up secure channel.')
        with open(key_path) as f:
            private_key = f.read().encode()
        with open('./server.crt') as f:
            certificate_chain = f.read().encode()
        server_creds = grpc.ssl_server_credentials(
            ((private_key, certificate_chain,),))
        server.add_secure_port(adress, server_creds)
    else:
        logging.info('Setting up insecure channel.')
        server.add_insecure_port(adress)


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    logging.basicConfig(level=logging.INFO)
    with open('settings.json') as f:
        data = json.load(f)
        logging.info(f'Config: {data}')
        settings = Settings.from_json(data)
    with open('languages.json') as f:
        data = json.load(f)
        provider = CommandProvider()
        provider.add_languages(*data)
    with open('limits.json') as f:
        data = json.load(f)
        logging.info(f'Limits: {data}')
        limits = Limits.from_json(data)
    logging.info(f'Local ip: {local_ip_address}')
    settings.ip = local_ip_address
    checker = CodeChecker(settings, limits, provider)
    sender = Sender(settings)

    logging.info('Creating workers')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servicer = GrpcServer(checker, settings)
    CodeTester_pb2_grpc.add_CodeTesterServicer_to_server(servicer, server)
    add_ports(server)

    logging.info('Starting server')
    server.start()
    sender.notify_started()
    server.wait_for_termination()
