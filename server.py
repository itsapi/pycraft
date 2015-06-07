from time import time
from math import radians
from threading import Thread

import terrain, saves, render, network

from console import debug


chunk_size = terrain.world_gen['chunk_size']
blocks = render.gen_blocks()

SUN_TICK = radians(1/32)
TPS = 10 # Ticks

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
        self._map = {x:s for x,s in self._map.items() if int(x) in range(*edges)}

    def get_meta(self, prop=None):
        return self._meta[prop] if prop else self._meta

    @property
    def players(self):
        return self._meta['players']

    @property
    def tick(self):
        return self._meta['tick']

    @property
    def map_(self):
        return self._map


class ServerInterface(CommonServer):
    """ Communicate with remote server. """

    def __init__(self, name, ip, port):
        self._sock = network.connect(ip, int(port))
        self._sock.setblocking(True)
        self._map = {}

        self._name = name
        self.login()

        self._dt = False

        self._meta = self._send('get_meta')
        self._me = self._meta['players'][self._name]
        self._last_tick = time()

        self.redraw = False
        self.view_change = False
        self.chunks_requested = set()

        self.listener_t = Thread(target=self.listener)
        self.listener_t.daemon = True
        self.listener_t.start()

    def _send(self, method, args=[], async=False):
        # Sync cannot be used once self.listener thread starts
        return network.send(self._sock, {'method': method, 'args': args}, async)

    def listener(self):
        """
            Data comes in in the form:

            {'event': 'event_name',
             'data':  'some data'}
        """
        while True:
            data = network.receive(self._sock)
            if data is None: break
            {   'blocks': self._set_blocks,
                'slices': self._set_slices,
                'player': self._set_player
            }[data['event']](data['data'])

    def load_chunks(self, chunk_list):
        slices_its_loading = ((chunk_num + chunk * chunk_size) for chunk in chunk_list for chunk_num in range(chunk_size))

        self._map.update({ str(i): list(terrain.EMPTY_SLICE) for i in slices_its_loading })
        self._send('load_chunks', [chunk_list], async=True)
        self.chunks_requested.update(chunk_list)
        self.view_change = True

    def chunk_loaded(self, x):
        return (x // terrain.world_gen['chunk_size']) not in self.chunks_requested

    def save_blocks(self, blocks):
        self._send('save_blocks', [blocks], async=True)
        self._set_blocks(blocks)

    def _set_blocks(self, blocks):
        self._map, _ = saves.set_blocks(self._map, blocks)
        self.view_change = True

    def _set_slices(self, new_slices):
        self._map.update(new_slices)
        self.chunks_requested.difference_update(terrain.get_chunk_list(new_slices.keys()))
        self.view_change = True

    def login(self):
        self._player = self._send('login', self._name)

    def dt(self):
        self._dt, self._last_tick, self._meta['tick'] = update_tick(self._last_tick, self._meta['tick'])
        return self._dt

    def _set_player(self, players):
        for name, player in players.items():
            self._meta['players'][name] = player

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

    def __init__(self, save, name):
        self._name = name
        self._save = save
        # {Loggedin player: socket}
        self._players = {}
        self._map = {}
        self._meta = saves.load_meta(save)
        self._last_tick = time()

        self.redraw = False
        self.view_change = False

        self.port, self.stop_server = network.start(self._handler)

        self.login(name)

    def _handler(self, sock, data):
        debug('Method: '+data['method'])

        return (
            self.login(data['args'], sock)
            if data['method'] == 'login' else
            {   'load_chunks': self.load_chunks,
                'get_meta': self.get_meta,
                'set_player': self.set_player,
                'save_blocks': self.save_blocks,
                'logout': lambda: self._logout(sock)
            }[data['method']](*data.get('args', []))
        )

    def _logout(self, sock):
        saves.save_meta(self._save, self._meta)
        self._players = {
            name: conn for name, conn in self._players.items() if conn != sock
        }

    def load_chunks(self, chunk_list):
        new_slices = {}
        gen_slices = {}

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

        # Save generated terrain to file
        if gen_slices: saves.save_map(self._save, gen_slices)

        self._map.update(new_slices)
        return { 'event': 'slices', 'data': new_slices }

    def save_blocks(self, blocks):
        self._map, new_slices = saves.set_blocks(self._map, blocks)
        saves.save_map(self._save, new_slices)
        self.view_change = True
        self.update_clients({ 'event': 'blocks', 'data': blocks })

    def chunk_loaded(self, x):
        return True

    def dt(self):
        dt, self._last_tick, self._meta['tick'] = update_tick(self._last_tick, self._meta['tick'])
        return dt

    def login(self, name, sock=None):
        debug('Logging in: '+name)
        if name not in self._players:
            # Load new player if new
            self._meta = saves.load_player(name, self._meta)
            debug('Creating: '+name)

            # Store socket
            if sock: self._players[name] = sock

            return self._meta['players'][name]

    def get_player(self, name):
        return self._meta['players'][name]

    def set_player(self, name, player):
        self._meta['players'][name] = player
        self.update_clients({ 'event': 'player', 'data': { name: player } }, name)

    def update_clients(self, message, sender=None):
        for name, sock in self._players.items():
            if name != sender: network.send(sock, message, True)

    @property
    def save(self):
        return self._save

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
        saves.save_meta(self._save, self._meta)

    @inv.setter
    def inv(self, inv):
        self._me['inv'] = inv
