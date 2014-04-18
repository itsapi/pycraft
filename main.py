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

    map_ = map_obj['slices']

    return meta, map_


def move_map(map_, edges):
    slices = {}
    for pos in range(*edges):
        pos = str(pos)
        slices[pos] = map_[pos]
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


def detect_edge(map_, pos, width, edges):
    edge = False
    if edges[0] < min(int(key) for key in map_.keys()):
        edge = edges[0]
    if edges[1] >= max(int(key) for key in map_.keys()):
        edge = edges[1]

    return edge


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
    width = 20

    FPS = 20

    last_out = time()
    with NonBlockingInput() as nbi:
        while True:

            pos += get_pos_d(nbi.char())

            edges = (pos - int(width / 2), pos + int(width / 2))
            edge = detect_edge(map_, pos, width, edges)
            if edge:
                map_[str(edge)] = gen_slice(edge, meta)

            chunk = move_map(map_, edges)

            if time() > last_out + (1 / FPS):
                last_out = time()
                render_map(chunk, blocks)

if __name__ == '__main__':
    main()
