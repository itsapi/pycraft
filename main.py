from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain


def get_x_delta(char):

    if char in 'aA':
        return -1
    if char in 'dD':
        return 1
    return 0


def get_y_delta(char):

    if char in 'wW':
        return -1
    return 0


def main():

    blocks = terrain.gen_blocks()

    # Menu loop
    while True:
        meta, map_, save = ui.main()

        x = meta['center']
        y = meta['height'] - meta['ground_height'] - 1
        width = 40
        FPS = 20

        old_edges = None
        redraw = False
        last_out = time()

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
                    slices[str(pos)] = terrain.gen_slice(pos, meta)
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
                if redraw and time() > 1/FPS + last_out:
                    redraw = False
                    last_out = time()
                    terrain.render_map(view, y, blocks)

                # Take inputs and change pos accordingly
                char = str(nbi.char())

                x += get_x_delta(char)
                dy = get_y_delta(char)
                y += dy
                if dy:
                    redraw = True

                if char == ' ':
                    redraw = True
                    if ui.pause() == 'exit':
                        game = False


if __name__ == '__main__':
    main()
