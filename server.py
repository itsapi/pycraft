from time import time
from math import radians, floor, ceil
from threading import Thread
from colours import colour_str, YELLOW

import terrain, saves, network

from console import log


SUN_TICK = radians(1/32)
TPS = 10  # Ticks


def _log_event(event, args):
    log('  Event:', colour_str(event, fg=YELLOW))
    log('  Args:', args)
    log()


def log_event_send(*args, label=None):
    log('Sending', '- [{}]'.format(label) if label else None)
    _log_event(*args)


def log_event_receive(*args, label=''):
    log('Received', '- [{}]'.format(label) if label else None)
    _log_event(*args)


class Server:
    def __init__(self, player, save, port, local_interface):

        self.current_players = {}
        self.local_player = player

        self.local_interface = local_interface
        self.game = Game(save, local_interface)
        self.default_port = port

        self.serving = False

    def _update_clients(self, message, exclude=None):
        log_event_send(message['event'], message['args'], label='Server')

        for name, sock in self.current_players.items():
            if name != exclude:
                network.send(sock, message)

        if self.local_player != exclude:
            self.local_interface.handle(message)

    def _player_list(self):
        return list(self.current_players.keys()) + [self.local_player]

    def handle(self, sock, data):
        log_event_receive(data['event'], data['args'], label='Server')

        result = (
            {'get_chunks': self.event_get_chunks,
             'set_player': self.event_set_player,
             'get_players': self.event_get_players,
             'set_blocks': self.event_set_blocks,
             'get_time': self.event_get_time,
             'logout': lambda: self.event_logout(sock),
             'login': lambda name: self.event_login(name, sock),
             'unload_slices': self.event_unload_slices
             }[data['event']](*data.get('args', []))
        )

        if result is not None:
            log_event_send(result['event'], result['args'], label='Server')
            return result

    # Handler and local interface mathods

    def event_login(self, name, sock):
        if name not in self.current_players.keys() and not name == self.local_player:
            log('Logging in: ' + name)

            if not name == self.local_player:
                # local_player already contains the local_player name
                self.current_players[name] = sock

            self._update_clients({'event': 'set_players', 'args': [{name: self.game.login(name)}]})
        else:
            log('Not Logging in: ' + name)
            return {'event': 'error', 'args': ['Username in use']}

    def event_logout(self, sock=None):
        # Re-add all players which aren't the sock
        players = {}
        for name, conn in self.current_players.items():
            if conn == sock:
                log('Logging out', name, sock)
                self._update_clients({'event': 'remove_player', 'args': [name]}, name)
            else:
                players[name] = sock

        self.current_players = players

    def event_set_blocks(self, blocks):
        self._update_clients({'event': 'set_blocks', 'args': [self.game.set_blocks(blocks)]})

    def event_get_chunks(self, chunk_list):
        return {'event': 'set_chunks', 'args': [self.game.get_chunks(chunk_list)]}

    def event_set_player(self, name, player):
        self.game.set_player(name, player)
        self._update_clients({'event': 'set_players', 'args': [{name: player}]}, exclude=name)

    def event_get_players(self):
        return {'event': 'set_players', 'args': [self.game.get_players(self._player_list())]}

    def event_unload_slices(self, edges):
        # TODO: Unload slices outside of edges if not loaded by other players
        pass

    def event_get_time(self):
        return {'event': 'set_time', 'args': [self.game.time]}

    # Methods for local interface only:

    def local_interface_login(self):
        self._update_clients({
            'event': 'set_players',
            'args': [{self.local_player: self.game.login(self.local_player)}]
        })

    def local_interface_init_server(self):
        self.serving = True
        self.port, self._stop_server = network.start(self.handle, self.default_port)

        log('Server started on port', self.port)

    def local_interface_kill_server(self):
        log('Server stopped')

        self.serving = False
        self._update_clients({'event': 'logout', 'args': ['Server Closed']}, exclude=self.local_player)
        self.current_players = {}

        self._stop_server()
        self.port, self._stop_server = None, None

    def local_interface_pause(self, paused):
        if not self.serving:
            self.game.pause(paused)

    def local_interface_map(self):
        return self.game._map

    def local_interface_dt(self):
        dt, time = self.game.dt()
        if dt and time % 100 == 0:
            self._update_clients({'event': 'set_time', 'args': [time]})
        return dt, time


class Game:
    """ The game. """

    def __init__(self, save, local_interface):
        self._save = save
        self._map = {}
        self._meta = saves.get_meta(save)
        self._last_tick = time()

        if self._meta.get('error'):
            local_interface.handle({'event': 'error', 'args': ['Invalid save format']})

    def get_chunks(self, chunk_list):
        new_slices = {}

        log('loading chunks', chunk_list)

        # Generates new terrain
        for chunk_n in chunk_list:

            chunk = saves.load_chunk(self._save, chunk_n)
            if not chunk:
                chunk = terrain.gen_chunk(chunk_n, self._meta)
                saves.save_chunk(self._save, chunk_n, chunk)
            new_slices.update(chunk)

        log('new slices', new_slices.keys())

        self._map.update(new_slices)
        return new_slices

    def set_blocks(self, blocks):
        self._map, new_slices = saves.set_blocks(self._map, blocks)
        saves.save_slices(self._save, new_slices)
        return blocks

    def set_player(self, name, player):
        self._meta['players'][name].update(player)
        saves.save_meta(self._save, self._meta)

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
        if time() >= (1/TPS) + self._last_tick:
            self._last_tick = time()
            self.time += 1
            self._dt = True

        else:
            self._dt = False

        return self._dt, self.time

    # TODO: keep track of the chunks loaded by players, only unload those that aren't loaded by others
    def unload_slices(self):
        pass

    @property
    def time(self):
        return self._meta['tick']

    @time.setter
    def time(self, time):
        self._meta['tick'] = time
