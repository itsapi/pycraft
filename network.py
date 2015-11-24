import socket
import threading
import socketserver
import struct
import json
import os

from console import log


SendLock = threading.Lock()


class SocketError(Exception):
    pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock


def send(sock, data):
    with SendLock:
        try:
            data = bytes(json.dumps(data), 'ascii')
            header = struct.pack('I', len(data))
            sock.sendall(header + data)

        except OSError:
            log('Socket closing')
            sock.close()


def receive(sock):
    data = None

    try:
        length = struct.unpack('I', sock.recv(4))[0]
        data = str(sock.recv(length), 'ascii')
    except OSError:
        log('Socket closing')
        sock.close()

    log('Received:', repr(''.join(data)))
    try:
        return json.loads(''.join(data))
    except ValueError as e:
        log('JSON Error:', e)


def requestHandlerFactory(data_handler):
    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def __init__(self, *args):
            self.data_handler = data_handler
            super().__init__(*args)

        def handle(self):
            while True:
                try:
                    data = receive(self.request)
                except SocketError:
                    break

                if data:
                    response = self.data_handler(self.request, data)

                    if response:
                        send(self.request, response)

            log('Handler Exiting')

    return ThreadedTCPRequestHandler


def start(data_handler, port):
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = '0.0.0.0', int(port)

    server = ThreadedTCPServer((HOST, PORT), requestHandlerFactory(data_handler))
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    return port, server.shutdown
