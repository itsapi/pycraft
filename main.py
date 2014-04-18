import json
from time import time
import random

from colors import colorStr, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
from console import WIDTH, HEIGHT
from nbinput import NonBlockingInput


default_meta = {
    'name': 'Untitled',
    'seed': '',
    'center': 0,
    'height': 30,
    'max_hill': 5,
    'ground_height': 10
}


def load_map(filename):
    map_obj = json.load(open(filename))
    
    meta = check_meta(map_obj)
    map_ = check_map(map_obj, meta)

    return meta, map_


def check_meta(map_obj):
    try:
        meta = map_obj['meta']

        # Create meta items if needed
        for key, default in default_meta.items():
            try:
                meta[key]
            except KeyError:
                meta[key] = default
    
    except KeyError:
        # Create default meta if needed
        meta = default_meta

    return meta


def check_map(map_obj, meta):
    try:
        map_ = map_obj['slices']

        for key, slice_ in map_.items():
            if not len(slice_) == meta['height']:

                if len(slice_) < meta['height']:
                    # Extend slice height
                    slice_ = [' '] * (meta['height'] - len(slice_)) + slice_
                elif len(slice_) > meta['height']:
                    # Truncate slice height
                    slice_ = slice_[:meta['height']]

                map_[key] = slice_

    except KeyError:
        map_ = {}

    return map_


def move_map(map_, edges):
    # Create subset of slices from map_ between edges
    slices = {}
    for pos in range(*edges):
        slices[pos] = map_[str(pos)]
    return slices


def render_map(map_, blocks):
    # Sorts the dict as a list by pos
    map_ = list(map_.items())
    map_.sort(key=lambda item: int(item[0]))

    # Seperates the pos and data
    map_ = tuple(zip(*map_))[1]

    # Orientates the data
    map_ = tuple(zip(*map_))

    print('\n'.join(''.join(blocks[pixel] for pixel in row) for row in map_))


def slice_height(pos, meta):
    slice_height_ = meta['ground_height']

    # Check surrounding slices for a hill
    for x in range(pos - meta['max_hill'], pos + meta['max_hill']):
        # Set seed for random numbers based on position
        random.seed(meta['seed'] + str(x))

        # Generate a hill with a 15% chance
        if random.randint(0, 100) < 15:
            # Set height to height of hill minus distance from hill
            hill_height = (meta['ground_height'] +
                random.randint(0, meta['max_hill']) - abs(pos-x))

            if hill_height > slice_height_:
                slice_height_ = hill_height

    return slice_height_


def gen_slice(pos, meta):
    slice_height_ = slice_height(pos, meta)

    # Form slice of sky - ground - stone layers
    slice_ = ([' '] * (meta['height'] - slice_height_) +
        ['-'] + ['#'] * (slice_height_ - 1))

    return slice_


def detect_edges(map_, edges):
    slices = []
    for pos in range(*edges):
        try:
            # If it doesn't exist add the pos to the list
            map_[str(pos)]
        except KeyError:
            slices.append(pos)
    
    return slices


def gen_blocks():
    return {
        ' ': ' ', # Air
        '-': colorStr('-', GREEN), # Grass
        '|': colorStr('|', MAGENTA), # Wood
        '@': colorStr('@', GREEN), # Leaves
        '#': colorStr('#', WHITE), # Stone
        'x': colorStr('x', BLACK), # Coal
        '+': colorStr('+', RED), # Iron
        ':': colorStr(':', RED), # Redstone
        '"': colorStr('"', YELLOW), # Gold
        'o': colorStr('o', CYAN) # Diamond
    }


def get_pos_d(char):
    if char == ',':
        return -1
    if char == '.':
        return 1
    return 0


def main():
    global SEED, HEIGHT, MAX_HILL, GROUND_HEIGHT

    blocks = gen_blocks()
    meta, map_ = load_map('map.blk')

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
            slices = detect_edges(map_, edges)
            for slice_pos in slices:
                map_[str(slice_pos)] = gen_slice(slice_pos, meta)
                redraw = True

            # Moving view
            if not edges == old_edges:
                redraw = True
                old_edges = edges
                view = move_map(map_, edges)

            # Draw view
            if redraw and time() > last_out + (1 / FPS):
                redraw = False
                last_out = time()
                render_map(view, blocks)

if __name__ == '__main__':
    main()
