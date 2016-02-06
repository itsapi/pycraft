from time import time
from math import radians
from random import random

from console import DEBUG, CLS, SHOW_CUR, HIDE_CUR, in_game_debug
from colours import init_colours
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render


def main():
    print(HIDE_CUR + CLS)

    saves.check_map_dir()

    meta = saves.get_global_meta()
    features = meta.get('features', {})

    init_colours(features.get('colours', True))

    blocks = render.gen_blocks()

    # Menu loop
    try:
        while True:
            game(blocks, features, *ui.main())

    finally:
        print(SHOW_CUR + CLS)


def game(blocks, features, meta, map_, save):
    x = meta['player_x']
    y = meta['player_y']
    dx = 0
    dy = 0
    dt = 0 # Tick
    df = 0 # Frame
    dc = 0 # Cursor
    ds = 0 # Selector
    dinv = False # Inventory
    dcraft = False # Crafting
    width = 40
    height = terrain.world_gen['height'] - 1
    FPS = 15 # Max
    TPS = 10 # Ticks
    IPS = 20 # Input
    MPS = 15 # Movement
    SUN_TICK = radians(1/32)

    old_bk_objects = None
    old_edges = None
    redraw = False
    last_frame = []
    last_out = time()
    last_tick = time()
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
    new_slices = {}
    alive = True
    events = []

    crafting_list, crafting_sel = player.get_crafting(
        meta['inv'],
        crafting_list,
        crafting_sel,
        blocks
    )

    # Game loop
    game = True
    with NonBlockingInput() as nbi:
        while game:
            # Finds display boundaries
            edges = (x - int(width / 2), x + int(width / 2))
            extended_edges = (edges[0]-render.max_light, edges[1]+render.max_light)

            # Generates new terrain
            slice_list = terrain.detect_edges(map_, extended_edges)
            for pos in slice_list:
                new_slices[pos] = terrain.gen_slice(pos, meta, blocks)
                map_[pos] = new_slices[pos]

            # Save new terrain to file
            if new_slices:
                saves.save_map(save, new_slices)
                new_slices = {}
                redraw = True

            # Moving view
            if not edges == old_edges:
                view = terrain.move_map(map_, edges)
                extended_view = terrain.move_map(map_, extended_edges)
                old_edges = edges
                redraw = True

            # Sun has moved
            bk_objects, sky_colour = render.bk_objects(meta['tick'], width)
            if not bk_objects == old_bk_objects:
                old_bk_objects = bk_objects
                redraw = True

            # Draw view
            if redraw and time() >= 1/FPS + last_out:
                df = 1
                redraw = False
                last_out = time()

                cursor_colour = player.cursor_colour(
                    x, y, cursor, map_, blocks, meta['inv'], inv_sel
                )

                objects = player.assemble_player(
                    int(width / 2), y, cursor, cursor_colour, c_hidden
                )

                lights = render.get_lights(extended_view, edges[0], blocks, bk_objects)

                out, last_frame = render.render_map(
                    view,
                    objects,
                    blocks,
                    bk_objects,
                    sky_colour,
                    lights,
                    meta['tick'],
                    last_frame
                )

                crafting_grid = render.render_grid(
                    player.CRAFT_TITLE, crafting, crafting_list, blocks,
                    height, crafting_sel
                )

                inv_grid = render.render_grid(
                    player.INV_TITLE, not crafting, meta['inv'], blocks,
                    height, inv_sel
                )

                label = (player.label(crafting_list, crafting_sel, blocks)
                        if crafting else
                        player.label(meta['inv'], inv_sel, blocks))

                out += render.render_grids(
                    [
                        [inv_grid, crafting_grid],
                        [[label]]
                    ],
                    width, height
                )

                print(out)
                in_game_debug('({}, {})'.format(x, y), 0, 0)
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                x, y = player.respawn(meta)

            if dt:
                # Player falls when no solid block below it
                if jump > 0:
                    # Countdown till fall
                    jump -= 1
                elif not terrain.is_solid(blocks, map_[x][y+1]):
                    # Fall
                    y += 1
                    redraw = True

                new_new_slices = process_events(events, map_, blocks)
                new_slices.update(new_new_slices)
                map_.update(new_new_slices)

            # If no block below, kill player
            try:
                block = map_[x][y+1]
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
                        str(inp), map_, x, y, blocks, jump)
                    y += dy
                    x += dx

                    last_move = time()

                new_new_slices, meta['inv'], inv_sel, new_events, dinv = \
                    player.cursor_func(str(inp), map_, x, y, cursor, inv_sel, meta, blocks)

                map_.update(new_new_slices)
                new_slices.update(new_new_slices)

                events += new_events

                dcraft, dcraftC, dcraftN = False, False, False
                if dinv: crafting = False
                if crafting:
                    # Craft if player pressed craft
                    meta['inv'], inv_sel, crafting_list, dcraftC = \
                        player.crafting(str(inp), meta['inv'], inv_sel,
                            crafting_list, crafting_sel, blocks)

                    # Increment/decrement craft no.
                    crafting_list, dcraftN = \
                        player.craft_num(str(inp), meta['inv'], crafting_list,
                            crafting_sel, blocks)

                    dcraft = dcraftC or dcraftN

                # Update crafting list
                if dinv or dcraft:
                    crafting_list, crafting_sel = \
                        player.get_crafting(meta['inv'], crafting_list,
                                            crafting_sel, blocks, dcraftC)
                    if not len(crafting_list): crafting = False

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                ds = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + ds) % len(crafting_list)
                                       if len(crafting_list) else 0)
                else:
                    inv_sel = ((inv_sel + ds) % len(meta['inv'])
                                  if len(meta['inv']) else 0)

                if any((dx, dy, dc, ds, dinv, dcraft)):
                    meta['player_x'], meta['player_y'] = x, y
                    saves.save_meta(save, meta)
                    redraw = True
                if dx or dy:
                    c_hidden = True
                if dc:
                    c_hidden = False

                last_inp = time()
                inp = None

            if char in 'c':
                redraw = True
                crafting = not crafting and len(crafting_list)

            # Hard pause
            if DEBUG and char in '\n':
                input()
                char = '0'

            # Pause game
            if char in ' \n':
                meta['player_x'], meta['player_y'] = x, y
                saves.save_meta(save, meta)
                redraw = True
                last_frame = []
                if ui.pause() == 'exit':
                    game = False

            # Increase tick
            if time() >= (1/TPS) + last_tick:
                dt = 1
                meta['tick'] += SUN_TICK
                last_tick = time()
            else:
                dt = 0


def process_events(events, map_, blocks):
    new_slices = {}

    for event in events:
        if event['time_remaining'] <= 0:
            ex, ey = event['pos']

            # Boom
            radius = 5
            blast_strength = 85
            for tx in range(ex - radius*2, ex + radius*2):
                for ty in range(ey - radius, ey + radius):

                    if (render.in_circle(tx, ty, ex, ey, radius) and tx in map_ and ty >= 0 and ty < len(map_[tx]) and
                            player.can_strength_break(map_[tx][ty], blast_strength, blocks)):

                        new_slices.setdefault(tx, map_[tx])

                        if not render.in_circle(tx, ty, ex, ey, radius - 1):
                            if random() < .5:
                                new_slices[tx][ty] = ' '
                        else:
                            new_slices[tx][ty] = ' '


            events.remove(event)
        else:
            event['time_remaining'] -= 1

    return new_slices


if __name__ == '__main__':
    main()
