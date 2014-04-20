from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain


def get_pos_delta(char, map_, x, y, blocks, jump):

    left_slice = map_[str(x - 1)]
    player_slice = map_[str(x)]
    right_slice = map_[str(x + 1)]

    feet_y = y
    head_y = y - 1
    below_y = y + 1
    above_y = y - 2

    dy = 0
    dx = 0

    is_solid = lambda block: terrain.is_solid(blocks, block)

    # Calculate change in x pos for left and right movement
    for test_char, dir_, func in (('aA', -1, left_slice), ('dD', 1, right_slice)):
        if (char in test_char
            and not is_solid( func[head_y] )):

            if is_solid( func[feet_y] ):
                if not is_solid( func[above_y] ):
                    dy = -1
                    dx = dir_
            else:
                dx = dir_

    # Jumps if up pressed, block below, no block above
    if (char in 'wW' and y > 1
        and blocks[ player_slice[below_y] ][1]
        and not blocks[ player_slice[above_y] ][1]):

        dy = -1
        jump = 5

    return dx, dy, jump


def break_block(inp, map_, x, y, blocks):
    block_x = str(x)
    block_y = y + 1

    new_slices = {}

    # If pressing x and block is breakable
    if inp in 'fF' and blocks[ map_[block_x][block_y] ][2]:
        new_slices[block_x] = map_[block_x]
        new_slices[block_x][block_y] = ' '

    return new_slices


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
