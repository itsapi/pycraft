import json
from time import sleep

from colors import colorStr, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
from console import WIDTH, HEIGHT
from nbinput import NonBlockingInput


def load_map(filename):
    map_obj = json.load(open(filename))
    
    name = map_obj['meta']['name']
    center = map_obj['meta']['center']
    map_ = map_obj['slices']

    return name, center, map_


def move_map(map_, left_edge, right_edge):
    if left_edge < 0 or right_edge >= len(map_):
        return False

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

def main():
    blocks = gen_blocks()
    name, center, map_ = load_map('map.blk')
    pos = (0, 0)

    with NonBlockingInput() as nbi:
        while True:

            chunk = move_map(map_, 0, 40)
            render_map(chunk, blocks)
            sleep(0.1)

if __name__ == '__main__':
    main()