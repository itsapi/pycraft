from time import time
from math import radians
import sys

from console import CLS, SHOW_CUR, HIDE_CUR
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render


def main():
    print(HIDE_CUR)
    print(CLS)

    saves.check_map_dir()
    blocks = render.gen_blocks()

    # Menu loop
    try:
        while True:
            game(blocks, *ui.main())

    finally:
        print(SHOW_CUR)
        print(CLS)


def game(blocks, meta, map_, save):
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
    FPS = 30 # Max
    TPS = 10 # Ticks
    IPS = 30 # Input
    MPS = 15 # Movement
    SUN_TICK = radians(1/32)

    old_sun = None
    old_edges = None
    redraw = False
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
                new_slices[str(pos)] = terrain.gen_slice(pos, meta, blocks)
                map_[str(pos)] = new_slices[str(pos)]

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
            sun = render.sun(meta['tick'], width)
            if not sun == old_sun:
                old_sun = sun
                redraw = True

            # Draw view
            if redraw and time() >= 1/FPS + last_out:
                df = 1
                redraw = False
                last_out = time()

                cursor_colour, can_break = player.cursor_colour(
                    x, y, cursor, map_, blocks, meta['inv'], inv_sel
                )

                objects = player.assemble_player(
                    int(width / 2), y, cursor, cursor_colour, c_hidden
                )

                if crafting:
                    label = player.label(
                        crafting_list, crafting_sel, blocks)
                else:
                    label = player.label(
                        meta['inv'], inv_sel, blocks)

                crafting_grid = render.render_grid(
                    player.CRAFT_TITLE, crafting, crafting_list, blocks,
                    terrain.world_gen['height']-1,
                    crafting_sel if crafting else None
                )

                inv_grid = render.render_grid(
                    player.INV_TITLE, not crafting, meta['inv'], blocks,
                    terrain.world_gen['height']-1, None if crafting else inv_sel
                )

                lights = render.get_lights(extended_view, edges[0], blocks)

                render.render_map(
                    view,
                    objects,
                    [[inv_grid, crafting_grid],
                     [[label]]],
                    blocks,
                    sun,
                    lights,
                    meta['tick']
                )
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                x, y = player.respawn(meta)

            # Player falls when no solid block below it
            if dt and not terrain.is_solid(blocks, map_[str(x)][y+1]):
                if jump > 0:
                    # Countdown till fall
                    jump -= 1
                else:
                    # Fall
                    y += 1
                    redraw = True

            # If no block below, kill player
            try:
                block = map_[str(x)][y+1]
            except IndexError:
                alive = False

            # Take inputs and change pos accordingly
            char = str(nbi.char()).lower()
            # Receive input if a key is pressed
            inp = char if char in 'wadkjliuo-=' else None

            # Input Frame
            if time() >= (1/IPS) + last_inp and alive and inp:

                if time() >= (1/MPS) + last_move:
                    dx, dy, jump = player.get_pos_delta(
                        str(inp), map_, x, y, blocks, jump)
                    y += dy
                    x += dx

                    last_move = time()

                new_slices, meta['inv'], inv_sel, dinv = \
                    player.cursor_func(
                        str(inp), map_, x, y, cursor,
                        can_break, inv_sel, meta, blocks
                    )

                map_.update(new_slices)

                dcraft = False
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
                                            crafting_sel, blocks)

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                ds = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + ds) % len(crafting_list)
                                       if len(crafting_list) else 0)
                else:
                    inv_sel = ((inv_sel + ds) % len(meta['inv'])
                                  if len(meta['inv']) else 0)

                if dx or dy or dc or ds or dinv or dcraft:
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
                crafting = not crafting

            # Pause game
            if char in ' \n':
                meta['player_x'], meta['player_y'] = x, y
                saves.save_meta(save, meta)
                redraw = True
                if ui.pause() == 'exit':
                    game = False

            # Increase tick
            if time() >= (1/TPS) + last_tick:
                dt = 1
                meta['tick'] += SUN_TICK
                last_tick = time()
            else:
                dt = 0


if __name__ == '__main__':
    main()
