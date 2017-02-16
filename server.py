from time import time
from math import radians, floor, ceil
from threading import Thread

import terrain, saves, network, mobs, items

from colours import colour_str, TERM_YELLOW
from console import log
from data import timings
from player import MAX_PLAYER_HEALTH


def _log_event(event, args):
    log('  Event:', colour_str(event, fg=TERM_YELLOW))
    log('  Args:', args)
    log()


def log_event_send(*args, label=None):
    log('Sending', '- [{}]'.format(label) if label else None)
    _log_event(*args)


def log_event_receive(*args, label=''):
    log('Received', '- [{}]'.format(label) if label else None)
    _log_event(*args)


def dt(last_tick):
    dt = 0
    t = time()
    tick_period = 1 / timings['tps']

    if t >= tick_period + last_tick:
        dt = int((t - last_tick) // tick_period)

        last_tick += dt * tick_period

    return dt, last_tick


class Server:
    def __init__(self, player, save, port, settings, local_interface):
        self.current_players = {}
        self.local_player = player

        self.local_interface = local_interface
        self.game = Game(save, settings)
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
             'get_mobs': self.event_get_mobs,
             'get_items': self.event_get_items,
             'set_blocks': self.event_set_blocks,
             'get_time': self.event_get_time,
             'player_attack': self.event_player_attack,
             'respawn': self.event_respawn,
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

            self._update_clients({'event': 'set_players', 'args': [{name: self.game.get_player(name)}]})
        else:
            log('Not Logging in: ' + name)
            return {'event': 'error', 'args': [{'event': 'login', 'message': 'Username in use'}]}

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
        return {'event': 'set_chunks', 'args': list(self.game.get_chunks(chunk_list))}

    def event_set_player(self, name, player):
        self.game.set_player(name, player)
        self._update_clients({'event': 'set_players', 'args': [{name: player}]}, exclude=name)

    def event_get_players(self):
        return {'event': 'set_players', 'args': [self.game.get_players(self._player_list())]}

    def event_get_mobs(self):
        return {'event': 'set_mobs', 'args': [self.game.mobs]}

    def event_get_items(self):
        return {'event': 'add_items', 'args': [self.game.items]}

    def event_unload_slices(self, name, edges):
        player = self.game.get_player(name)
        player['edges'] = edges
        self.game.set_player(name, player)
        self.game.reload_slices()

    def event_get_time(self):
        return {'event': 'set_time', 'args': [self.game.time]}

    def event_respawn(self, name):
        player = self.game.get_player(name)

        self.game._meta['items'].update(
            items.new_item(player['x'], player['y'], player['inv'], self.game._last_tick, ttl=5*60))
        player['inv'] = []
        player['x'], player['y'] = self.game.spawn
        player['health'] = MAX_PLAYER_HEALTH

        self._update_clients({'event': 'set_players', 'args': [{name: player}]})

    def event_player_attack(self, name, x, y, radius, strength):
        updated_players, updated_mobs = self.game.player_attack(name, x, y, radius, strength)
        self._update_clients({'event': 'set_players', 'args': [updated_players]})
        self._update_clients({'event': 'set_mobs', 'args': [updated_mobs]})

    # Methods for local interface only:

    def local_interface_login(self):
        self._update_clients({
            'event': 'set_players',
            'args': [{self.local_player: self.game.get_player(self.local_player)}]
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

    def local_interface_slice_heights(self):
        return self.game._slice_heights

    def local_interface_mobs(self):
        return self.game.mobs

    def local_interface_dt(self):
        dt, time = self.game.dt()
        if dt and time % 100 == 0:
            self._update_clients({'event': 'set_time', 'args': [time]})
        return dt, time

    def local_interface_update_mobs(self):
        updated_players, new_items = self.game.update_mobs()
        self._update_clients({'event': 'set_players', 'args': [updated_players]})
        self._update_clients({'event': 'set_mobs', 'args': [self.game.mobs]})
        self._update_clients({'event': 'add_items', 'args': [new_items]})

    def local_interface_spawn_mobs(self):
        self.game.spawn_mobs()
        self._update_clients({'event': 'set_mobs', 'args': [self.game.mobs]})

    def local_interface_update_items(self):
        removed_items = self.game.update_items()
        self._update_clients({'event': 'remove_items', 'args': [removed_items]})

    def local_interface_items(self):
        return self.game.items


class Game:
    """ The game. """

    def __init__(self, save, settings):
        self._save = save
        self._map = {}
        self._slice_heights = {}
        self._meta = saves.get_meta(save)
        self._last_tick = time()
        self._settings = settings

    def get_chunks(self, chunk_list):
        new_slices = {}
        new_slice_heights = {}

        log('loading chunks', chunk_list)

        # Generates new terrain
        for chunk_n in chunk_list:

            chunk, chunk_slice_heights = saves.load_chunk(self._save, chunk_n)
            if not chunk:
                chunk, chunk_slice_heights = terrain.gen_chunk(chunk_n, self._meta)
                saves.save_chunk(self._save, chunk_n, chunk, chunk_slice_heights)

            new_slices.update(chunk)
            new_slice_heights.update(chunk_slice_heights)

        log('new slices', new_slices.keys())

        self._map.update(new_slices)
        self._slice_heights.update(new_slice_heights)
        return {key: ''.join(value) for key, value in new_slices.items()}, new_slice_heights

    def set_blocks(self, blocks):
        self._map, new_slices = saves.set_blocks(self._map, blocks)
        saves.save_slices(self._save, new_slices, self._slice_heights)
        return blocks

    def set_player(self, name, player):
        self._meta['players'][name].update(player)
        saves.save_meta(self._save, self._meta)

    def get_player(self, name):
        self._meta = saves.load_player(name, self._meta)
        return self._meta['players'][name]

    def get_players(self, players):
        """ Returns player objects """
        return {name: self._meta['players'][name] for name in players}

    # TODO: pause and unpause implementation
    def pause(self, paused):
        pass

    def dt(self):
        self._dt, self._last_tick = dt(self._last_tick)
        self.time += self._dt

        return self._dt, self.time

    def reload_slices(self):
        new_map = {}
        for x, slice_ in self._map.items():
            if any(x in range(*player['edges']) for player in self._meta['players'].values() if player.get('edges')):
                new_map[x] = slice_
        self._map = new_map

    def player_attack(self, name, ax, ay, radius, strength):
        return mobs.calculate_player_attack(name, ax, ay, radius, strength, self._meta['players'], self._meta['mobs'])

    def update_mobs(self):
        if not self._settings.get('mobs'):
            self._meta['mobs'].clear()
            return {}, {}

        updated_players, new_items = mobs.update(self._meta['mobs'], self._meta['players'], self._map, self._last_tick)
        self._meta['items'].update(new_items)
        return updated_players, new_items

    def spawn_mobs(self):
        if self._settings.get('mobs'):
            return mobs.spawn(self._meta['mobs'], self._map)
        else:
            return {}

    def update_items(self):
        removed_items = items.pickup_items(self._meta['items'], self._meta['players'])
        removed_items += items.despawn_items(self._meta['items'], self._last_tick)
        return removed_items

    @property
    def mobs(self):
        return self._meta['mobs']

    @property
    def items(self):
        return self._meta['items']

    @property
    def spawn(self):
        return self._meta['spawn'], 1

    @property
    def time(self):
        return self._meta['tick']

    @time.setter
    def time(self, time):
        self._meta['tick'] = time
