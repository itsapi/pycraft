import socket
import threading
import socketserver
import struct
import json
import os

from console import log
import time


SendLock = threading.Lock()


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
            log('sending data length', len(data))
            header = struct.pack('I', len(data))
            sock.sendall(header + data)
        except OSError:
            log('Socket closing')
            sock.close()


def receive(sock):
    data = None
    error = False
    bufsize = 1024

    try:
        d = sock.recv(4)
    except OSError:
        error = True
    else:
        if not d:
            error = True

    if not error:
        length = struct.unpack('I', d)[0]
        log('data length', length)
        d = bytes()

        try:
            for _ in range(length // bufsize):
                d += sock.recv(bufsize)
                time.sleep(0.001)
            d += sock.recv(length % bufsize)
        except OSError:
            error = True
        else:
            if not len(d):
                error = True

        if not error:
            data = str(d, 'ascii')
            log('real length', len(d))

    if error:
        log('Socket closing')
        sock.close()

    else:
        log('Received:', repr(data), trunc=False)
        try:
            return json.loads(data)
        except ValueError as e:
            log('JSON Error:', e)


def requestHandlerFactory(data_handler):
    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def __init__(self, *args):
            self.data_handler = data_handler
            super().__init__(*args)

        def handle(self):
            while True:
                data = receive(self.request)

                if data:
                    response = self.data_handler(self.request, data)

                    if response:
                        send(self.request, response)
                else:
                    break

            log('Handler Exiting')

    return ThreadedTCPRequestHandler


def start(data_handler, port):
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = '0.0.0.0', int(port)

    server = ThreadedTCPServer((HOST, PORT), requestHandlerFactory(data_handler))
    _, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    return port, server.shutdown
