from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain, player


def main():

    saves.check_map_dir()
    blocks = terrain.gen_blocks()

    # Menu loop
    while True:
        meta, map_, save = ui.main()

        x = meta['player_x']
        y = meta['player_y']
        dx = 0
        dy = 0
        dt = 0
        df = 0
        dc = 0
        width = 40
        FPS = 10
        TPS = 10

        old_edges = None
        redraw = False
        last_out = time()
        last_tick = time()
        last_inp = time()
        tick = 0
        inp = None
        jump = 0
        cursor = 0
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
                    new_slices[str(pos)] = terrain.gen_slice(pos, meta)
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

                # Draw view
                if redraw and time() >= 1/FPS + last_out:
                    df = 1
                    redraw = False
                    last_out = time()
                    objects = player.render_player(int(width / 2), y, cursor)
                    terrain.render_map(view, objects, blocks)
                else:
                    df = 0

                # Respawn player if dead
                if not alive and df:
                    alive = True
                    x, y = player.respawn(meta)

                # If no block below, kill player
                try:
                    block = map_[str(x)][y+1]
                    below_solid = terrain.is_solid(blocks, block)
                except IndexError:
                    below_solid = False
                    alive = False

                # Player falls when no solid block below it
                if dt and not below_solid:
                    if jump > 0:
                        jump -= 1
                    else:
                        y += 1
                        redraw = True

                # Take inputs and change pos accordingly
                char = str(nbi.char()).lower()

                inp = char if char in 'wadkjl' else None

                if time() >= (1/TPS) + last_inp and alive:
                    if inp:
                        dx, dy, jump = player.get_pos_delta(
                            str(inp), map_, x, y, blocks, jump)
                        y += dy
                        x += dx

                        new_slices = player.break_block(str(inp),
                                     map_, x, y, cursor, blocks)
                        map_.update(new_slices)

                        dc = player.move_cursor(inp)
                        cursor = (cursor + dc) % 6

                        if dx or dy or dc:
                            redraw = True
                        if dx or dy:
                            meta['player_x'], meta['player_y'] = x, y
                            saves.save_meta(save, meta)

                        last_inp = time()
                        inp = None

                # Pause game
                if char == ' ':
                    redraw = True
                    if ui.pause() == 'exit':
                        game = False

                # Increase tick
                if time() >= (1/TPS) + last_tick:
                    dt = 1
                    tick += dt
                    last_tick = time()
                else:
                    dt = 0


if __name__ == '__main__':
    main()
