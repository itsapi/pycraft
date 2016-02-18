import cProfile

from time import time, sleep
from math import radians
from random import random

import console as c
from colours import init_colours
from console import DEBUG, log, in_game_log, CLS, SHOW_CUR, HIDE_CUR
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render, server_interface


def main():
    print(HIDE_CUR + CLS)

    log('Start\n')

    # Menu loop
    try:
        meta = saves.get_global_meta()
        settings = saves.get_settings()

        profile = c.getenv_b('PYCRAFT_PROFILE')

        name = c.getenv('PYCRAFT_NAME') or settings.get('name') or ui.name(settings)
        port = c.getenv('PYCRAFT_PORT') or meta.get('port') or 0

        init_colours(settings)
        saves.check_map_dir()

        while True:
            data = ui.main(meta, settings)

            if data is None:
                break

            if data['local']:
                # Local Server
                server_obj = server_interface.LocalInterface(name, data['save'], port)
            else:
                # Remote Server
                server_obj = server_interface.RemoteInterface(name, data['ip'], data['port'])

            if not server_obj.error:
                if profile:
                    cProfile.runctx('game(server_obj, settings)', globals(), locals(), filename='game.profile')
                else:
                    game(server_obj, settings)

            if server_obj.error:
                ui.error(server_obj.error)

    finally:
        print(SHOW_CUR + CLS)


def game(server, settings):
    x, y = server.pos
    dx = 0
    dy = 0
    dt = 0  # Tick
    df = 0  # Frame
    dc = 0  # Cursor
    ds = 0  # Selector
    dinv = False  # Inventory
    dcraft = False  # Crafting
    width = 40
    height = terrain.world_gen['height'] - 1
    FPS = 15  # Max
    IPS = 20  # Input
    MPS = 15  # Movement

    old_bk_objects = None
    old_edges = None
    last_frame = {}
    last_out = time()
    last_inp = time()
    last_move = time()
    inp = None
    jump = 0
    cursor = 0
    crafting = False
    crafting_sel = 0
    crafting_list = []
    inv_sel = 0
    c_hidden = True
    new_blocks = {}
    alive = True
    events = []

    crafting_list, crafting_sel = player.get_crafting(
        server.inv,
        crafting_list,
        crafting_sel
    )

    # Game loop
    with NonBlockingInput() as nbi:
        while server.game:
            x, y = server.pos

            sleep(1/1000)
            # Finds display boundaries
            edges = (x - int(width / 2), x + int(width / 2))
            extended_edges = (edges[0]-render.max_light, edges[1]+render.max_light)

            slice_list = terrain.detect_edges(server.map_, extended_edges)
            if slice_list:
                log('slices to load', slice_list)
                chunk_list = terrain.get_chunk_list(slice_list)
                server.get_chunks(chunk_list)
                server.unload_slices(extended_edges)

            # Moving view
            if not edges == old_edges or server.view_change:
                extended_view = terrain.move_map(server.map_, extended_edges)
                old_edges = edges
                server.redraw = True
                server.view_change = False

            # Sun has moved
            bk_objects, sky_colour = render.bk_objects(server.time, width, settings.get('fancy_lights', True))
            if not bk_objects == old_bk_objects:
                old_bk_objects = bk_objects
                server.redraw = True

            # Draw view
            if server.redraw and time() >= 1/FPS + last_out:
                df = 1
                server.redraw = False
                last_out = time()

                if settings.get('gravity', False):
                    blocks = terrain.apply_gravity(server.map_, edges)
                    if blocks: server.set_blocks(blocks)

                cursor_colour = player.cursor_colour(
                    x, y, cursor, server.map_, server.inv, inv_sel
                )

                objects = player.assemble_players(
                    server.current_players, x, y, int(width / 2), edges
                )

                if not c_hidden:
                    objects.append(player.assemble_cursor(
                        int(width / 2), y, cursor, cursor_colour
                    ))

                lights = render.get_lights(extended_view, edges[0], bk_objects)

                out, last_frame = render.render_map(
                    server.map_,
                    server.slice_heights,
                    edges,
                    objects,
                    bk_objects,
                    sky_colour,
                    lights,
                    last_frame,
                    settings.get('fancy_lights', True)
                )

                crafting_grid = render.render_grid(
                    player.CRAFT_TITLE, crafting, crafting_list,
                    height, crafting_sel
                )

                inv_grid = render.render_grid(
                    player.INV_TITLE, not crafting, server.inv,
                    height, inv_sel
                )

                label = (player.label(crafting_list, crafting_sel)
                        if crafting else
                        player.label(server.inv, inv_sel))

                out += render.render_grids(
                    [
                        [inv_grid, crafting_grid],
                        [[label]]
                    ],
                    width, height
                )

                print(out)
                in_game_log('({}, {})'.format(x, y), 0, 0)
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                server.respawn()

            if dt and server.chunk_loaded(x):
                # Player falls when no solid block below it
                if jump > 0:
                    # Countdown till fall
                    jump -= 1
                elif not terrain.is_solid(server.map_[x][y+1]):
                    # Fall
                    y += 1
                    server.pos = x, y
                    server.redraw = True

                new_blocks = process_events(events, server.map_)

                if new_blocks:
                    server.set_blocks(new_blocks)

            # If no block below, kill player
            try:
                block = server.map_[x][y+1]
            except IndexError:
                alive = False

            # Receive input if a key is pressed
            char = str(nbi.char()).lower()
            inp = char if char in 'wadkjliuo-=' else None

            # Input Frame
            if time() >= (1/IPS) + last_inp and alive and inp:

                if time() >= (1/MPS) + last_move:
                    # Update player position
                    dx, dy, jump = player.get_pos_delta(
                        str(inp), server.map_, x, y, jump)
                    y += dy
                    x += dx

                    last_move = time()

                new_blocks, inv, inv_sel, new_events, dinv = \
                    player.cursor_func(
                        str(inp), server.map_, x, y, cursor, inv_sel, server.inv
                    )

                if dinv:
                    server.inv = inv

                if new_blocks:
                    server.set_blocks(new_blocks)

                events += new_events

                dcraft, dcraftC, dcraftN = False, False, False
                if dinv: crafting = False
                if crafting:
                    # Craft if player pressed craft
                    inv, inv_sel, crafting_list, dcraftC = \
                        player.crafting(str(inp), server.inv, inv_sel,
                            crafting_list, crafting_sel)
                    if dcraftC:
                        server.inv = inv

                    # Increment/decrement craft no.
                    crafting_list, dcraftN = \
                        player.craft_num(str(inp), server.inv, crafting_list,
                            crafting_sel)

                    dcraft = dcraftC or dcraftN

                # Update crafting list
                if dinv or dcraft:
                    crafting_list, crafting_sel = \
                        player.get_crafting(server.inv, crafting_list,
                                            crafting_sel, dcraftC)
                    if not len(crafting_list): crafting = False

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                ds = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + ds) % len(crafting_list)
                                       if len(crafting_list) else 0)
                else:
                    inv_sel = ((inv_sel + ds) % len(server.inv)
                                  if len(server.inv) else 0)

                if any((dx, dy, dc, ds, dinv, dcraft)):
                    server.pos = x, y
                    server.redraw = True
                if dx or dy:
                    c_hidden = True
                if dc:
                    c_hidden = False

                last_inp = time()
                inp = None

            if char in 'c':
                server.redraw = True
                crafting = not crafting and len(crafting_list)

            # Hard pause
            if DEBUG and char in '\n':
                input()
                char = '0'

            # Pause game
            if char in ' \n':
                server.pos = x, y
                server.redraw = True
                last_frame = {}
                if ui.pause(server, settings) == 'exit':
                    server.logout()

            dt = server.dt()


def process_events(events, map_):
    new_blocks = {}

    for event in events:
        if event['time_remaining'] <= 0:
            ex, ey = event['pos']

            # Boom
            radius = 5
            blast_strength = 85
            for tx in range(ex - radius*2, ex + radius*2):
                new_blocks[tx] = {}

                for ty in range(ey - radius, ey + radius):

                    if (render.in_circle(tx, ty, ex, ey, radius) and tx in map_ and ty >= 0 and ty < len(map_[tx]) and
                            player.can_strength_break(map_[tx][ty], blast_strength)):

                        if not render.in_circle(tx, ty, ex, ey, radius - 1):
                            if random() < .5:
                                new_blocks[tx][ty] = ' '
                        else:
                            new_blocks[tx][ty] = ' '

            events.remove(event)
        else:
            event['time_remaining'] -= 1

    return new_blocks


if __name__ == '__main__':
    main()
