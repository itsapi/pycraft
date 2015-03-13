from time import time
from math import radians
import sys

from nbinput import NonBlockingInput
import saves, ui, terrain, player


def main():

    # Hide cursor
    print('\033[?25l')

    saves.check_map_dir()
    blocks = terrain.gen_blocks()

    # Menu loop
    while True:
        game(blocks, *ui.main(exit))


def exit():
    # Show cursor
    print('\033[?25h')

    sys.exit()


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
    inv_sel = 0
    c_hidden = True
    new_slices = {}
    alive = True

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
                inv = player.render_inv(inv_sel, meta['inv'], blocks)
                terrain.render_map(view, objects, inv, blocks, sun, tick)
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                x, y = player.respawn(meta)

            # Player falls when no solid block below it
            if dt and not terrain.is_solid(blocks, map_[str(x)][y+1]):
                if jump > 0:
                    jump -= 1
                else:
                    y += 1
                    redraw = True

            # If no block below, kill player
            try:
                block = map_[str(x)][y+1]
                below_solid = terrain.is_solid(blocks, block)
            except IndexError:
                below_solid = False
                alive = False

            # Take inputs and change pos accordingly
            char = str(nbi.char()).lower()
            # receive input if key pressed is w a d k j l h ; b or enter
            inp = char if char in 'wadkjlh;b'+chr(2) else None

            if time() >= (1/TPS) + last_inp and alive and inp:
                dx, dy, jump = player.get_pos_delta(
                    str(inp), map_, x, y, blocks, jump)
                y += dy
                x += dx

                new_slices, meta['inv'], meta['ext_inv'], dinv = \
                    player.cursor_func(
                        str(inp), map_, x, y, cursor, inv_sel, meta, blocks
                    )

                map_.update(new_slices)

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                di = player.move_inv_sel(inp)
                inv_sel = (inv_sel + di) % player.INV_SLOTS

                if dx or dy or dc or di or dinv:
                    meta['player_x'], meta['player_y'] = x, y
                    saves.save_meta(save, meta)
                    redraw = True
                if dx or dy:
                    c_hidden = True
                if dc:
                    c_hidden = False

                last_inp = time()
                inp = None

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
