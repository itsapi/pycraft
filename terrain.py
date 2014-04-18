import random
from colors import colorStr, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE


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
