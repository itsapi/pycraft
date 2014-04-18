import json
from time import time
import random

from colors import colorStr, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
from console import WIDTH, HEIGHT
from nbinput import NonBlockingInput


def load_map(filename):
    map_obj = json.load(open(filename))
    
    meta = map_obj['meta']
    map_ = map_obj['slices']

    return meta, map_


def move_map(map_, left_edge, right_edge):
    slices = {}
    for pos in range(left_edge, right_edge):
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


def slice_height(seed, pos, max_hill, ground_height):
    slice_height_ = ground_height
    for x in range(pos - max_hill, pos + max_hill):
        random.seed(seed + str(x))
        if random.randint(0, 100) < 15:
            hill_height = ground_height + random.randint(0, max_hill) - abs(pos-x)
            if hill_height > slice_height_:
                slice_height_ = hill_height

    return slice_height_


def gen_slice(seed, pos, height, max_hill, ground_height):
    slice_height_ = slice_height(seed, pos, max_hill, ground_height)
    slice_ = [' '] * (height - slice_height_) + ['-'] + ['#'] * (slice_height_ - 1)

    return slice_

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
    blocks = gen_blocks()
    meta, map_ = load_map('map.blk')

    pos = meta['center']
    width = 20

    FPS = 20
    SEED = meta['seed']
    HEIGHT = len(map_['0'])
    MAX_HILL = 5
    GROUND_HEIGHT = 13

    last_out = time()
    with NonBlockingInput() as nbi:
        while True:

            pos += get_pos_d(nbi.char())

            edge = False
            left_edge, right_edge = pos - int(width / 2), pos + int(width / 2)
            if left_edge < 0:
                edge = left_edge
            if right_edge > len(map_) - 2:
                edge = right_edge
            if edge:
                map_[str(edge)] = gen_slice(SEED, edge, HEIGHT, MAX_HILL, GROUND_HEIGHT)

            chunk = move_map(map_, left_edge, right_edge)

            if time() > last_out + (1 / FPS):
                last_out = time()
                render_map(chunk, blocks)

if __name__ == '__main__':
    main()