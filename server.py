from time import time

from math import radians

import terrain, saves, render


chunk_size = terrain.world_gen['chunk_size']
blocks = render.gen_blocks()

SUN_TICK = radians(1/32)
TPS = 10 # Ticks


class RemoteServer:
    def __init__(self, name, addr):
        self._name = name
        self._remote = addr

    def load_chunks(self, slice_list):
        pass


class Server:
    def __init__(self, save, name):
        self._players = {}
        self._name = name
        self._save = save
        self._map = {}
        self._meta = saves.load_meta(save)
        self._last_tick = time()

        self.login(name)

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

    @property
    def save(self):
        return self._save

    @property
    def me(self):
        return self._players[self._name]

    @property
    def pos(self):
        return self.me['player_x'], self.me['player_y']

    @pos.setter
    def pos(self, pos):
        self.me['player_x'], self.me['player_y'] = pos

    @property
    def inv(self):
        return self.me['inv']

    @inv.setter
    def inv(self, inv):
        self.me['inv'] = inv

    @property
    def map_(self):
        return self._map

    def save_blocks(self, blocks):
        self._map = saves.save_blocks(self._save, self._map, blocks)

