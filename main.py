from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain


def get_pos_d(char):

    if char == ',':
        return -1
    if char == '.':
        return 1
    return 0


def main():

    blocks = terrain.gen_blocks()

    meta, map_, save = ui.main()

    pos = meta['center']
    width = 40

    FPS = 20

    old_edges = None
    redraw = False
    last_out = time()

    with NonBlockingInput() as nbi:
        while True:

            pos += get_pos_d(nbi.char())

            # Finds display boundaries
            edges = (pos - int(width / 2), pos + int(width / 2))

            # Generates new terrain
            slices = {}
            slice_pos_list = terrain.detect_edges(map_, edges)
            for slice_pos in slice_pos_list:
                slices[str(slice_pos)] = terrain.gen_slice(slice_pos, meta)
                map_[str(slice_pos)] = slices[str(slice_pos)]
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
            if redraw and time() > last_out + (1 / FPS):
                redraw = False
                last_out = time()
                terrain.render_map(view, blocks)


if __name__ == '__main__':
    main()
