from time import time
from math import radians, floor, ceil
from threading import Thread

import terrain, saves, network

from console import debug


chunk_size = terrain.world_gen['chunk_size']

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


def _debug_event(event, args):
    debug('  Event:', event)
    debug('  Args:', args)
    debug()


def debug_event_send(*args, label=None):
    debug('Sending', '- [{}]'.format(label) if label else None)
    _debug_event(*args)


def debug_event_receive(*args, label=''):
    debug('Received', '- [{}]'.format(label) if label else None)
    _debug_event(*args)


class Server:
    def __init__(self, player, save, port, local_interface):

        self.current_players = {}
        self.local_player = player

        self.local_interface = local_interface
        self.game = Game(save)
        self.default_port = port

        self.serving = False

    def _update_clients(self, message, exclude=None):
        debug_event_send(message['event'], message['args'], label='Server')

        for name, sock in self.current_players.items():
            if name != exclude:
                network.send(sock, message)

        if self.local_player != exclude:
            self.local_interface.handle(message)

    def _player_list(self):
        return list(self.current_players.keys()) + [self.local_player]

    def handle(self, sock, data):
        debug_event_receive(data['event'], data['args'], label='Server')

        return (
            {'get_chunks': self.event_get_chunks,
             'set_player': self.event_set_player,
             'get_players': self.event_get_players,
             'set_blocks': self.event_set_blocks,
             'logout': lambda: self.event_logout(sock),
             'login': lambda data: self.event_login(data, sock),
             'unload_slices': self.event_unload_slices
             }[data['event']](*data.get('args', []))
        )

    # Handler and local interface mathods

    def event_login(self, name, sock):
        if name not in self.current_players.keys() and not name == self.local_player:
            debug('Logging in: ' + name)

            if not name == self.local_player:
                # local_player already contains the local_player name
                self.current_players[name] = sock

            self._update_clients({'event': 'set_players', 'args': [{name: self.game.login(name)}]})
        else:
            debug('Not Logging in: '+name)
            return {'event': 'error', 'args': [{'event': 'login', 'message': 'Username in use'}]}

    def event_logout(self, sock=None):
        # Re-add all players which aren't the sock
        players = {}
        for name, conn in self.current_players.items():
            if conn == sock:
                debug('Logging out', name, sock)
                self._update_clients({'event': 'remove_player', 'args': [name]}, name)
            else:
                players[name] = sock

        self.current_players = players

    def event_set_blocks(self, blocks):
        return {'event': 'set_blocks', 'args': [self.game.set_blocks(blocks)]}

    def event_get_chunks(self, chunk_list):
        return {'event': 'set_chunks', 'args': [self.game.get_chunks(chunk_list)]}

    def event_set_player(self, name, player):
        self.game.set_player(name, player)

    def event_get_players(self):
        return {'event': 'set_players', 'args': [self.game.get_players(self._player_list())]}

    def event_unload_slices(self, edges):
        # TODO: Unload slices outside of edges if not loaded by other players
        pass

    # Methods for local interface only:

    def local_interface_login(self):
        self._update_clients({
            'event': 'set_players',
            'args': [{self.local_player: self.game.login(self.local_player)}]
        })

    def local_interface_init_server(self):
        self.serving = True
        self.port, self._stop_server = network.start(self.handle, self.default_port)

        debug('Server started on port', self.port)

    def local_interface_kill_server(self):
        debug('Server stopped')

        self.serving = False
        self._update_clients({'event': 'logout', 'args': ['Server Closed']})
        self.current_players = {}

        self._stop_server()
        self.port, self._stop_server = None, None

    def local_interface_pause(self, paused):
        if not self.serving:
            self.game.pause(paused)

    def local_interface_map(self):
        return self.game._map


class Game:
    """ The game. """

    def __init__(self, save):
        self._save = save
        self._map = {}
        self._meta = saves.load_meta(save)
        self._last_tick = time()

    def get_chunks(self, chunk_list):
        new_slices = {}
        gen_slices = {}

        debug('loading chunks', chunk_list)

        # Generates new terrain
        for chunk_num in chunk_list:
            chunk = saves.load_chunk(self._save, chunk_num)
            for i in range(chunk_size):
                pos = i + chunk_num * chunk_size
                if not str(pos) in chunk:
                    slice_ = terrain.gen_slice(pos, self._meta)
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
        return new_slices

    def set_blocks(self, blocks):
        self._map, new_slices = saves.set_blocks(self._map, blocks)
        saves.save_map(self._save, new_slices)
        return blocks

    def set_player(self, name, player):
        self._meta['players'][name].update(player)

    # NOTE: Should probably be renamed to get_player
    def login(self, name):
        self._meta = saves.load_player(name, self._meta)
        return self._meta['players'][name]

    def get_players(self, players):
        """ Returns player objects """
        return {name: self._meta['players'][name] for name in players}

    # TODO: pause and unpause implementation
    def pause(self, paused):
        pass

    # TODO: Needs rethinking
    def dt(self):
        dt, self._last_tick, self._meta['tick'] = update_tick(self._last_tick, self._meta['tick'])
        return dt

    # TODO: keep track of the chunks loaded by players, only unload those that aren't loaded by others
    def unload_slices(self):
        pass
