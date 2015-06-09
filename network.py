import socket
import threading
import socketserver
import json
import os

from console import debug


END = '<END>'


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock


def send(sock, data, async):
    try:
        data = bytes(json.dumps(data) + END, 'ascii')
        debug('Sending:', repr(data))
        sock.sendall(data)

        if not async:
            return receive(sock)

    except OSError:
        debug('Socket closing')
        sock.close()


def receive(sock):
    total_data = []
    data = ''
    while True:
        debug('Waiting')
        try:
            data = str(sock.recv(1024), 'ascii')
        except OSError:
            debug('Socket closing')
            sock.close()

        if END in data:
            total_data.append(data[:data.find(END)])
            break
        total_data.append(data)
        if len(total_data) > 1:
            # Check if end_of_data was split
            last_pair = total_data[-2] + total_data[-1]
            if END in last_pair:
                total_data[-2] = last_pair[:last_pair.find(END)]
                total_data.pop()
                break
        elif len(data) == 0:
            return None

    debug('Received:', repr(''.join(total_data)))
    return json.loads(''.join(total_data))


def requestHandlerFactory(data_handler):
    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def __init__(self, *args):
            self.data_handler = data_handler
            super().__init__(*args)

        def handle(self):
            while True:
                try:
                    data = receive(self.request)
                    if not data: break
                except ValueError:
                    pass

                response = self.data_handler(self.request, data)
                if not response: continue

                send(self.request, response, True)

            debug('Handler Exiting')
            data_handler(self.request, {'method': 'logout'})

    return ThreadedTCPRequestHandler


def start(data_handler):
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = '0.0.0.0', int(os.getenv('PYCRAFT_PORT', 0))

    server = ThreadedTCPServer((HOST, PORT), requestHandlerFactory(data_handler))
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    return port, server.shutdown
