from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain


def get_pos_delta(char, slices, y, blocks, jump):

    player_slice = slices[1]
    left_slice = slices[0]
    right_slice = slices[2]

    feet_y = y
    head_y = y-1
    below_y = y+1
    above_y = y-2

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


def main():

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

        # Game loop
        game = True
        with NonBlockingInput() as nbi:
            while game:

                # Finds display boundaries
                edges = (x - int(width / 2), x + int(width / 2))

                # Generates new terrain
                slices = {}
                slice_list = terrain.detect_edges(map_, edges)
                for pos in slice_list:
                    slices[str(pos)] = terrain.gen_slice(pos, meta, blocks)
                    map_[str(pos)] = slices[str(pos)]
                    redraw = True

                # Save new terrain to file
                if slices:
                    saves.save_map(save, slices)

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

                inp = char if char in 'wWaAdD' else None

                if time() >= (1/TPS) + last_inp:
                    if inp:
                        dx, dy, jump = get_pos_delta(
                            str(inp),
                            [map_[str(x + i)] for i in range(-1, 2)],
                            y, blocks, jump
                        )
                        y += dy
                        x += dx
                        if dy or dx:
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
