from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain, player


def main():

    saves.check_map_dir()
    blocks = terrain.gen_blocks()

    # Menu loop
    while True:
        meta, map_, save = ui.main()

        x = meta['center']
        y = 1
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
        new_slices = {}

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
                    redraw = True

                # Save new terrain to file
                if new_slices:
                    saves.save_map(save, new_slices)
                    new_slices = {}

                # Moving view
                if not edges == old_edges:
                    redraw = True
                    old_edges = edges
                    view = terrain.move_map(map_, edges)

                # Draw view
                if redraw and time() >= 1/FPS + last_out:
                    redraw = False
                    last_out = time()
                    terrain.render_map(view, int(width / 2), y, blocks)

                # Increase tick
                if time() >= (1/TPS) + last_tick:
                    dt = 1
                    tick += dt
                    last_tick = time()
                else:
                    dt = 0

                # Player falls when no block below it
                if dt and not blocks[map_[str(x)][y+1]][1]:
                    if jump > 0:
                        jump -= 1
                    else:
                        y += 1
                        redraw = True

                # Take inputs and change pos accordingly
                char = str(nbi.char())

                inp = char if char in 'wWaAdDfF' else None

                if time() >= (1/TPS) + last_inp:
                    if inp:
                        dx, dy, jump = get_pos_delta(
                            str(inp), map_, x, y, blocks, jump)
                        y += dy
                        x += dx

                        new_slices = break_block(str(inp), map_, x, y, blocks)
                        map_.update(new_slices)

                        if dx or dy or break_block:
                            redraw = True
                        last_inp = time()
                        inp = None

                # Pause game
                if char == ' ':
                    redraw = True
                    if ui.pause() == 'exit':
                        game = False


if __name__ == '__main__':
    main()
