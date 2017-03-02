from threading import Thread, Event
from math import radians, floor, ceil
from time import time

from server import Server, log_event_send, log_event_receive, dt
from console import log
from data import timings
from player import MAX_PLAYER_HEALTH

import saves, terrain, network, mobs

chunk_size = terrain.world_gen['chunk_size']


class RemoteInterface:
    """
        Communicate with remote server.

        Uses self._send to communicate with Server
    """

    def __init__(self, name, ip, port):
        self.map_ = {}
        self.slice_heights = {}
        self.current_players = {}
        self.mobs = {}
        self.items = {}
        self.game = True
        self.error = None
        self._name = name

        # We cannot serve, we are connected to a server.
        # TODO: Maybe we can do this better...?
        self.serving = None

        try:
            self._sock = network.connect(ip, int(port))
        except (ConnectionRefusedError, ValueError):
            self.error = 'Cannot connect to server'
            return

        self._sock.setblocking(True)

        self.finished_login = Event()

        self._listener_t = Thread(target=self._listener)
        self._listener_t.daemon = True
        self._listener_t.start()

        # Login
        self._send('login', [self._name])

        # Server doesn't respond
        if not self.finished_login.wait(3):
            self.error = 'No response from server on login'
            log(self.error)

            self._sock.close()
            return

        # Server responds with error
        if self.error is not None:
            log('Error response from server on login:', self.error)

            self._sock.close()
            return

        # Login successful!

        self.time = timings['tick']
        self._dt = False
        self._last_tick = time()

        self._chunks_requested = set()

        self._send('get_players')
        self._send('get_mobs')
        self._send('get_items')
        self._send('get_time')

        self.redraw = False
        self.view_change = False

    def _send(self, event, args=[]):
        log_event_send(event, args, label='RemoteInterface')

        network.send(self._sock, {'event': event, 'args': args})

    def _listener(self):
        while True:
            data = network.receive(self._sock)

            if data is None:
                break

            log_event_receive(data['event'], data['args'], label='RemoteInterface')

            {'set_blocks': self._event_set_blocks,
             'set_chunks': self._event_set_chunks,
             'set_players': self._event_set_players,
             'remove_player': self._event_remove_player,
             'set_mobs': self._event_set_mobs,
             'set_items': self._event_set_items,
             'add_items': self._event_add_items,
             'remove_items': self._event_remove_items,
             'set_time': self._event_set_time,
             'logout': self._event_logout,
             'error': self._event_error
             }[data['event']](*data.get('args', []))

            if data['event'] == 'error':
                break

    # Handler network request methods:

    def _event_set_blocks(self, blocks):
        self.map_, _ = saves.set_blocks(self.map_, blocks)
        self.view_change = True

    def _event_set_chunks(self, new_chunks, new_slice_heights):
        self.map_.update({int(key): list(value) for key, value in new_chunks.items()})
        self.slice_heights.update({int(key): value for key, value in new_slice_heights.items()})

        self._chunks_requested.difference_update(terrain.get_chunk_list(new_chunks.keys()))
        self.view_change = True

    def _event_set_players(self, players):
        self.current_players.update(players)
        self.redraw = True

        # TODO: Move the login checks out of this method
        if self._name in players and not self.finished_login.is_set():
            log('FINISHED LOGIN')
            self.finished_login.set()

    def _event_remove_player(self, name):
        self.current_players.pop(name)
        self.redraw = True

    def _event_set_mobs(self, mobs):
        self.mobs = mobs
        self.redraw = True

    def _event_set_items(self, items):
        self.items = items
        self.redraw = True

    def _event_add_items(self, new_items):
        self.items.update(new_items)
        self.redraw = True

    def _event_remove_items(self, removed_items):
        self.items = {id_: item for id_, item in self.items.items() if id_ not in removed_items}
        self.redraw = True

    def _event_set_time(self, time):
        self.time = time

    def _event_logout(self, error=None):
        self.game = False

        if error is not None:
            self.error = error

        try:
            self._sock.close()
        except OSError:
            pass

    def _event_error(self, error):
        self.finished_login.set()

        self.error = 'Error from server: ' + error['event'] + ': ' + error['message']
        log(self.error)
        self.game = False

    # Main loop methods:

    def get_chunks(self, chunk_list):
        slices_its_loading = [(chunk_num + chunk * chunk_size) for chunk in chunk_list for chunk_num in range(chunk_size)]

        self.map_.update({i: list(terrain.EMPTY_SLICE) for i in slices_its_loading})
        self.slice_heights.update({i: terrain.world_gen['ground_height'] for i in slices_its_loading})
        self._send('get_chunks', [chunk_list])
        self._chunks_requested.update(chunk_list)
        self.view_change = True

    def chunk_loaded(self, x):
        return (x // terrain.world_gen['chunk_size']) not in self._chunks_requested

    def unload_slices(self, edges):
        edges = [chunk_size * floor(edges[0] / chunk_size),
                 chunk_size * ceil(edges[1] / chunk_size)]
        self.map_ = {x: s for x, s in self.map_.items() if x in range(*edges)}
        self.slice_heights = {x: h for x, h in self.slice_heights.items() if x in range(*edges)}

        # TODO: Figure out if we always need to send this...
        self._send('unload_slices', [self._name, edges])

    def set_blocks(self, blocks):
        self._send('set_blocks', [blocks])
        self._event_set_blocks(blocks)

    def logout(self):
        self._send('logout')
        self._event_logout()

    def dt(self):
        self._dt, self._last_tick = dt(self._last_tick)
        self.time += self._dt

        return self._dt

    def update_mobs(self):
        # The client does nothing
        pass

    def spawn_mobs(self, *_):
        # The client does nothing
        pass

    def despawn_items(self):
        # The client does nothing
        pass

    def player_attack(self, raduis, strength):
        x, y = self.pos
        self._send('player_attack', [self._name, x, y, raduis, strength])

    def respawn(self):
        self._send('respawn', [self._name])

    def add_health(self, dhealth):
        new_health = self.current_players[self._name]['health'] + dhealth
        self.current_players[self._name]['health'] = min(MAX_PLAYER_HEALTH, new_health)

        self._send('set_player', [self._name, self.current_players[self._name]])

    @property
    def pos(self):
        return self.current_players[self._name]['x'], self.current_players[self._name]['y']

    @property
    def inv(self):
        return self.current_players[self._name]['inv']

    @property
    def health(self):
        return self.current_players[self._name]['health']

    @pos.setter
    def pos(self, pos):
        self.current_players[self._name]['x'], self.current_players[self._name]['y'] = pos
        self._send('set_player', [self._name, self.current_players[self._name]])

    @inv.setter
    def inv(self, inv):
        self.current_players[self._name]['inv'] = inv
        self._send('set_player', [self._name, self.current_players[self._name]])

    # TODO: do the pause stuff
    def pause(self, paused):
        self.local_pause = paused


class LocalInterface:
    """
        Communicate with local server.

        Communicates directly with self._server
    """

    def __init__(self, name, save, port, settings):
        self.game = True
        self.error = None
        self.serving = False
        self.time = timings['tick']
        self._name = name
        self.current_players = {}
        self._server = Server(name, save, port, settings, self)
        self._server.local_interface_login()

    def _send(self, event, args=[]):
        log_event_send(event, args, label='LocalInterface')
        return self._server.handle(None, {'event': event, 'args': args})

    def handle(self, data):
        log_event_receive(data['event'], data['args'], label='LocalInterface')

        {'set_blocks': self._event_view_change,
         'set_chunks': self._event_view_change,
         'set_players': self._event_set_players,
         'remove_player': self._event_remove_player,
         'set_mobs': self._event_set_mobs,
         'set_items': self._event_set_items,
         'add_items': self._event_add_items,
         'remove_items': self._event_remove_items,
         'set_time': self._event_set_time,
         'logout': self._event_logout,
         'error': self._event_error
         }[data['event']](*data.get('args', []))

    # Handler network request methods:

    def _event_view_change(self, *args):
        self.view_change = True

    def _event_set_players(self, players):
        self.current_players.update(players)
        self.redraw = True

    def _event_remove_player(self, name):
        self.current_players.pop(name)
        self.redraw = True

    def _event_set_mobs(self, mobs):
        self.redraw = True

    def _event_set_items(self, items):
        self.redraw = True

    def _event_add_items(self, new_items):
        self.redraw = True

    def _event_remove_items(self, remove_items):
        self.redraw = True

    def _event_set_time(self, time):
        self.time = time

    def _event_logout(self, error=None):
        if error is not None:
            self.error = error
        self.game = False

    def _event_error(self, error):
        self.error = 'Error from server: ' + error['event'] + ': ' + event['message']
        log(self.error)
        self.game = False

    # Main loop methods:

    def get_chunks(self, chunk_list):
        slices_its_loading = ((chunk_num + chunk * chunk_size) for chunk in chunk_list for chunk_num in range(chunk_size))

        self.handle(self._send('get_chunks', [chunk_list]))
        self.view_change = True

    def chunk_loaded(self, x):
        return True

    def unload_slices(self, edges):
        edges = [chunk_size * floor(edges[0] / chunk_size),
                 chunk_size * ceil(edges[1] / chunk_size)]
        self._send('unload_slices', [self._name, edges])

    def set_blocks(self, blocks):
        self._send('set_blocks', [blocks])

    def logout(self):
        if self.serving:
            self.kill_server()
        self._event_logout()

    def init_server(self):
        self.serving = True
        self._server.local_interface_init_server()

    def kill_server(self):
        self.serving = False
        self._server.local_interface_kill_server()

    def dt(self):
        dt, self.time = self._server.local_interface_dt()
        return dt

    def update_mobs(self):
        self._server.local_interface_update_mobs()

    def spawn_mobs(self, *args):
        self._server.local_interface_spawn_mobs(*args)

    def update_items(self):
        self._server.local_interface_update_items()

    def player_attack(self, radius, strength):
        x, y = self.pos
        self._send('player_attack', [self._name, x, y, radius, strength])

    def respawn(self):
        self._send('respawn', [self._name])

    def add_health(self, dhealth):
        new_health = self.current_players[self._name]['health'] + dhealth
        self.current_players[self._name]['health'] = min(MAX_PLAYER_HEALTH, new_health)

        self._send('set_player', [self._name, self.current_players[self._name]])

    @property
    def pos(self):
        return self.current_players[self._name]['x'], self.current_players[self._name]['y']

    @property
    def inv(self):
        return self.current_players[self._name]['inv']

    @pos.setter
    def pos(self, pos):
        self.current_players[self._name]['x'], self.current_players[self._name]['y'] = pos
        self._send('set_player', [self._name, self.current_players[self._name]])

    @inv.setter
    def inv(self, inv):
        self.current_players[self._name]['inv'] = inv

    @property
    def health(self):
        return self.current_players[self._name]['health']

    @property
    def map_(self):
        return self._server.local_interface_map()

    @property
    def slice_heights(self):
        return self._server.local_interface_slice_heights()

    @property
    def port(self):
        return self._server.port

    @property
    def mobs(self):
        return self._server.local_interface_mobs()

    @property
    def items(self):
        return self._server.local_interface_items()

    # TODO: do the pause stuff
    def pause(self, paused):
        self.local_pause = paused
