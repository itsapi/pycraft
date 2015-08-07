from time import time
from math import radians, floor, ceil
from threading import Thread

import terrain, saves, render, network

from console import debug


chunk_size = terrain.world_gen['chunk_size']
blocks = render.gen_blocks()

SUN_TICK = radians(1/32)
TPS = 10  # Ticks


def update_tick(last_tick, cur_tick):
    # Increase tick
    if time() >= (1/TPS) + last_tick:
        dt = 1
        cur_tick += SUN_TICK
        last_tick = time()
    else:
        dt = 0

    return dt, last_tick, cur_tick


class CommonServer:

    def unload_slices(self, edges):
        edges = [chunk_size * floor(edges[0] / chunk_size),
                 chunk_size * ceil(edges[1] / chunk_size)]
        self._map = {x: s for x, s in self._map.items() if int(x) in range(*edges)}

    def get_meta(self, prop=None):
        return self._meta[prop] if prop else self._meta

    @property
    def tick(self):
        return self._meta['tick']

    @property
    def map_(self):
        return self._map

    def init_server(self):
        pass

    def kill_server(self):
        pass


class ServerInterface(CommonServer):
    """ Communicate with remote server. """

    def __init__(self, name, ip, port):
        self._map = {}
        self.game = True
        self.server = None
        self.error = None
        self._name = name

        try:
            self._sock = network.connect(ip, int(port))
        except (ConnectionRefusedError, ValueError):
            self.error = 'Cannot connect to server'
            return

        self._sock.setblocking(True)

        if not self._login():
            self._sock.close()
            return

        self._dt = False

        self._meta = self._send('get_meta')
        self._me = self._meta['players'][self._name]
        self._last_tick = time()
        self._chunks_requested = set()

        self._current_players = set(self._send('get_players'))

        self.redraw = False
        self.view_change = False

        self._listener_t = Thread(target=self._listener)
        self._listener_t.daemon = True
        self._listener_t.start()

    def _send(self, method, args=[], async=False):
        # Sync cannot be used once self.listener thread starts
        return network.send(self._sock, {'method': method, 'args': args}, async)

    def _listener(self):
        """
            Data comes in in the form:

            {'event': 'event_name',
             'data':  'some data'}
        """
        while True:
            try:
                data = network.receive(self._sock)
            except server.SocketError:
                break

            {'blocks': self._set_blocks,
             'slices': self._set_slices,
             'player': self._set_player,
             'remove_player': self._remove_player,
             'logout': self._logout
             }[data['event']](*data.get('args', []))

    def load_chunks(self, chunk_list):
        slices_its_loading = ((chunk_num + chunk * chunk_size) for chunk in chunk_list for chunk_num in range(chunk_size))

        self._map.update({str(i): list(terrain.EMPTY_SLICE) for i in slices_its_loading})
        self._send('load_chunks', [chunk_list], async=True)
        self._chunks_requested.update(chunk_list)
        self.view_change = True

    def chunk_loaded(self, x):
        return (x // terrain.world_gen['chunk_size']) not in self._chunks_requested

    def save_blocks(self, blocks):
        self._send('save_blocks', [blocks], async=True)
        self._set_blocks(blocks)

    def _set_blocks(self, blocks):
        self._map, _ = saves.set_blocks(self._map, blocks)
        self.view_change = True

    def _set_slices(self, new_slices):
        self._map.update(new_slices)
        self._chunks_requested.difference_update(terrain.get_chunk_list(new_slices.keys()))
        self.view_change = True

    def _login(self):
        response = self._send('login', [self._name])
        try:
            self.error = response['err']
            return False
        except KeyError:
            self._player = response
            return True

    def _logout(self, error=None):
        self.game = False

        if error is not None:
            self.error = error

        try:
            self._sock.close()
        except OSError:
            pass

    def logout(self):
        self._send('logout', async=True)
        self._logout()

    def dt(self):
        self._dt, self._last_tick, self._meta['tick'] = update_tick(self._last_tick, self._meta['tick'])
        return self._dt

    def _set_player(self, name, player):
        self._meta['players'][name] = player
        self._current_players.add(name)
        self.redraw = True

    def _remove_player(self, name):
        self._current_players.discard(name)
        self.redraw = True

    @property
    def players(self):
        return {name: self._meta['players'][name] for name in self._current_players}

    @property
    def pos(self):
        return self._me['player_x'], self._me['player_y']

    @property
    def inv(self):
        return self._me['inv']

    @pos.setter
    def pos(self, pos):
        self._me['player_x'], self._me['player_y'] = pos
        self._send('set_player', [self._name, self._me], async=True)

    @inv.setter
    def inv(self, inv):
        self._me['inv'] = inv
        self._send('set_player', [self._name, self._me], async=True)


class Server(CommonServer):
    """ The host server. """

    FAKE_SOCKET = 'FAKE'

    def __init__(self, name, save, port):
        self.game = True
        self.server = False
        self.error = None

        self.default_port = port
        self.port = self.default_port

        self._name = name
        self._save = save
        # {Loggedin player: socket}
        self._current_players = {}
        self._map = {}
        self._meta = saves.load_meta(save)
        self._last_tick = time()

        self.redraw = False
        self.view_change = False

        self._login(self._name, Server.FAKE_SOCKET)

    def init_server(self):
        self.port, self._stop_server = network.start(self._handler, self.default_port)
        debug('Server started on port', self.port)
        self.server = True

    def kill_server(self):
        self._update_clients({'event': 'logout', 'args': ['Server Closed']})
        self._current_players = {self._name: Server.FAKE_SOCKET}
        self._stop_server()
        self.server = False
        self.port, self._stop_server = None, None

    def _handler(self, sock, data):
        debug('Method: '+data['method'])
        debug(data)

        return (
            {'load_chunks': self.load_chunks,
             'get_meta': self.get_meta,
             'set_player': self._set_player,
             'get_players': self._get_players,
             'save_blocks': self.save_blocks,
             'logout': lambda: self._logout(sock),
             'login': lambda data: self._login(data, sock)
             }[data['method']](*data.get('args', []))
        )

    def _update_clients(self, message, sender=None):
        for name, sock in self._current_players.items():
            if name != sender and sock is not Server.FAKE_SOCKET:
                network.send(sock, message, True)

    def load_chunks(self, chunk_list):
        new_slices = {}
        gen_slices = {}

        debug('loading chunks', chunk_list)

        # Generates new terrain
        for chunk_num in chunk_list:
            chunk = saves.load_chunk(self._save, chunk_num)
            for i in range(chunk_size):
                pos = i + chunk_num * chunk_size
                if not str(pos) in chunk:
                    slice_ = terrain.gen_slice(pos, self._meta, blocks)
                    chunk[str(pos)] = slice_
                    gen_slices[str(pos)] = slice_
            new_slices.update(chunk)

        debug('generated slices', gen_slices.keys())
        debug('new slices', new_slices.keys())

        # Save generated terrain to file
        if gen_slices:
            debug('saving slices', gen_slices.keys())
            saves.save_map(self._save, gen_slices)

        self._map.update(new_slices)
        return {'event': 'slices', 'args': [new_slices]}

    def save_blocks(self, blocks):
        self._map, new_slices = saves.set_blocks(self._map, blocks)
        saves.save_map(self._save, new_slices)
        self.view_change = True
        self._update_clients({'event': 'blocks', 'args': [blocks]})

    def chunk_loaded(self, x):
        return True

    def dt(self):
        dt, self._last_tick, self._meta['tick'] = update_tick(self._last_tick, self._meta['tick'])
        return dt

    def _login(self, name, sock):
        if name not in self._current_players:
            debug('Logging in: '+name)
            # Load new player if new
            self._meta = saves.load_player(name, self._meta)

            # Store socket
            self._current_players[name] = sock

            return self._meta['players'][name]
        else:
            debug('Not Logging in: '+name)
            return {'err': 'Username in use'}

    def _logout(self, sock=None):
        saves.save_meta(self._save, self._meta)

        # Re-add all players which aren't the sock
        players = {}
        for name, conn in self._current_players.items():
            if conn == sock:
                debug('Logging', name, sock)
                self._update_clients({'event': 'remove_player', 'args': [name]}, name)
                self.redraw = True
            else:
                players[name] = sock

        self._current_players = players

    def logout(self):
        if self.server:
            self.kill_server()
        self.game = False

    def _set_player(self, name, player):
        self._meta['players'][name] = player
        self._update_clients({'event': 'player', 'args': [name, player]}, name)
        self.redraw = True

    def _get_players(self):
        """ Returns logged in player names """
        return list(self._current_players.keys())

    @property
    def players(self):
        """ Returns logged in player objects """
        return {name: self._meta['players'][name] for name in self._current_players.keys()}

    @property
    def _me(self):
        return self._meta['players'][self._name]

    @property
    def pos(self):
        return self._me['player_x'], self._me['player_y']

    @property
    def inv(self):
        return self._me['inv']

    @pos.setter
    def pos(self, pos):
        self._me['player_x'], self._me['player_y'] = pos
        self._set_player(self._name, self._me)
        saves.save_meta(self._save, self._meta)

    @inv.setter
    def inv(self, inv):
        self._me['inv'] = inv
