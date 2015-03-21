from time import time
from math import radians
import sys

from console import CLS, SHOW_CUR, HIDE_CUR
from nbinput import NonBlockingInput
import saves, ui, terrain, player


def main():
    print(HIDE_CUR)
    print(CLS)

    saves.check_map_dir()
    blocks = terrain.gen_blocks()

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
    di = 0 # Inventory Selector
    dinv = False # Inventory
    dcraft = False
    width = 40
    FPS = 10
    TPS = 10
    SUN_TICK = radians(1/32)

    old_sun = None
    old_edges = None
    redraw = False
    last_out = time()
    last_tick = time()
    last_inp = time()
    tick = 0
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

    crafting_list, crafting_sel = player.get_crafting(meta['inv'], crafting_sel, blocks)

    # Game loop
    game = True
    with NonBlockingInput() as nbi:
        while game:
            # Finds display boundaries
            edges = (x - int(width / 2), x + int(width / 2))

            # Generates new terrain
            slice_list = terrain.detect_edges(map_, edges)
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
                old_edges = edges
                redraw = True

            # Sun has moved
            sun = terrain.sun(tick, width)
            if not sun == old_sun:
                old_sun = sun
                redraw = True

            # Draw view
            if redraw and time() >= 1/FPS + last_out:
                df = 1
                redraw = False
                last_out = time()
                objects = player.render_player(int(width / 2), y, cursor, c_hidden)

                crafting_grid = player.render_grid(crafting_list, blocks, crafting_sel if crafting else None)
                inv_grid = player.render_grid(meta['inv'], blocks, None if crafting else inv_sel)

                terrain.render_map(view, objects, inv_grid, crafting_grid, blocks, sun, tick)
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
            # receive input if key pressed is w a d k j l i u o
            inp = char if char in 'wadkjliuo' else None

            if time() >= (1/TPS) + last_inp and alive and inp:
                dx, dy, jump = player.get_pos_delta(
                    str(inp), map_, x, y, blocks, jump)
                y += dy
                x += dx

                new_slices, meta['inv'], inv_sel, dinv = \
                    player.cursor_func(
                        str(inp), map_, x, y, cursor, inv_sel, meta, blocks
                    )

                if crafting:
                    meta['inv'], inv_sel, crafting_list, dcraft = \
                        player.crafting(
                            str(inp), meta['inv'], inv_sel, crafting_list, crafting_sel, blocks
                        )

                if dinv or dcraft:
                    crafting_list, crafting_sel = player.get_crafting(meta['inv'], crafting_sel, blocks)

                map_.update(new_slices)

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                di = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + di) % len(crafting_list)) if len(crafting_list) else 0
                else:
                    inv_sel = ((inv_sel + di) % len(meta['inv'])) if len(meta['inv']) else 0

                if dx or dy or dc or di or dinv or dcraft:
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
                tick += SUN_TICK
                last_tick = time()
            else:
                dt = 0


if __name__ == '__main__':
    main()
