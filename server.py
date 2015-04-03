from time import time
from math import radians

import terrain, saves, render, network


chunk_size = terrain.world_gen['chunk_size']
blocks = render.gen_blocks()

SUN_TICK = radians(1/32)
TPS = 10 # Ticks


class RemoteServer:
    """ Comunicate with remote server. """

    def __init__(self, name, ip, port):
        self._sock = network.connect(ip, port)
        self._map = {}
        self._name = name
        self._meta = self._send('get_meta')
        self._me = self._send('get_player', [self._name])

    def _send(self, method, args=[]):
        return network.send(self._sock, {'method': method, 'args': args})

    def load_chunks(self, slice_list):
        self._map.update(self._send('load_chunks', [slice_list]))

    def tick(self):
        return self._send('tick')

    def login(self):
        self._player = self._send('login', [self._name])

    def get_meta(self, prop=None):
        return self._send('get_meta', [prop])

    @property
    def pos(self):
        return self._me['player_x'], self._me['player_y']

    @pos.setter
    def pos(self, pos):
        self._me['player_x'], self._me['player_y'] = pos
        self._send('set_player', [self._name, self._me])

    @property
    def inv(self):
        return self._me['inv']

    @inv.setter
    def inv(self, inv):
        self._me['inv'] = inv
        self._send('set_player', [self._name, self._me])

    @property
    def map_(self):
        return self._map

    def save_blocks(self, blocks):
        self._send('save_blocks', [blocks])


class Server:
    """ The 'remote' server. """
    def __init__(self, save, name):
        self._players = {}
        self._name = name
        self._save = save
        self._map = {}
        self._meta = saves.load_meta(save)
        self._last_tick = time()

        self.port, self.stop_server = network.start(self._handler)

        self.login(name)

    def _handler(self, data):
        return {
            'load_chunks': self.load_chunks,
            'tick': self.tick,
            'login': self.login,
            'get_meta': self.get_meta,
            'set_meta': self.set_meta,
            'get_player': self.get_player,
            'set_player': self.set_player,
            'save_blocks': self.save_blocks
        }[data['method']](*data.get('args', []))

    def load_chunks(self, slice_list):
        new_slices = {}
        gen_slices = {}

        # Generates new terrain
        for chunk_num in set(i // chunk_size for i in slice_list):
            chunk = saves.load_chunk(self._save, chunk_num)
            for i in range(chunk_size):
                pos = i + chunk_num * chunk_size
                if not str(pos) in chunk:
                    slice_ = terrain.gen_slice(pos, self._meta, blocks)
                    chunk[str(pos)] = slice_
                    gen_slices[str(pos)] = slice_
            new_slices.update(chunk)

        # Save generated terrain to file
        if gen_slices:
            saves.save_map(self._save, gen_slices)

        self._map.update(new_slices)
        return new_slices

    def tick(self):
        # Increase tick
        if time() >= (1/TPS) + self._last_tick:
            dt = 1
            self._meta['tick'] += SUN_TICK
            self._last_tick = time()
        else:
            dt = 0

        return dt

    def login(self, name):
        if name not in self._players:
            self._players[name] = saves.load_player(name, self._meta)
            return self._players[name]

    def get_meta(self, prop=None):
        return self._meta[prop] if prop else self._meta

    def set_meta(self, prop, value):
        self._meta[prop] = value

    def get_player(self, name):
        return self._players[name]

    def set_player(self, name, player):
        self._players[name] = player

    @property
    def save(self):
        return self._save

    @property
    def _me(self):
        return self._players[self._name]

    @property
    def pos(self):
        return self._me['player_x'], self._me['player_y']

    @pos.setter
    def pos(self, pos):
        self._me['player_x'], self._me['player_y'] = pos

    @property
    def inv(self):
        return self._me['inv']

    @inv.setter
    def inv(self, inv):
        self._me['inv'] = inv

    @property
    def map_(self):
        return self._map

    def save_blocks(self, blocks):
        self._map = saves.save_blocks(self._save, self._map, blocks)

    def update_clients(self, blocks):
        pass
