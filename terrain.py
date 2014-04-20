import random
import copy
from math import ceil

from console import CLS
from colors import *


world_gen = {
    'height': 30,
    'max_hill': 15,
    'ground_height': 10,
    'ores': {
        'coal': {
            'char': 'x',
            'vain_size': 4,
            'chance': 0.05,
            'upper': 30,
            'lower': 0
        },
        'iron': {
            'char': '+',
            'vain_size': 3,
            'chance': 0.03,
            'upper': 15,
            'lower': 0
        },
        'redstone': {
            'char': ':',
            'vain_size': 4,
            'chance': 0.03,
            'upper': 7,
            'lower': 0
        },
        'gold': {
            'char': '"',
            'vain_size': 2,
            'chance': 0.02,
            'upper': 10,
            'lower': 0
        },
        'diamond': {
            'char': 'o',
            'vain_size': 1,
            'chance': 0.01,
            'upper': 5,
            'lower': 0
        },
        'emerald': {
            'char': 'o',
            'vain_size': 1,
            'chance': 0.002,
            'upper': 7,
            'lower': 0
        },
    }
}

trees = (
    ((0, 1, 1),
     (1, 1, 0),
     (0, 1, 1)),
    ((1, 1, 0, 0, 0, 1, 1),
     (0, 1, 1, 0, 1, 1, 0),
     (0, 0, 1, 1, 0, 0, 0),
     (0, 1, 1, 1, 1, 0, 0),
     (1, 1, 0, 0, 1, 1, 0))
)


def move_map(map_, edges):

    # Create subset of slices from map_ between edges
    slices = {}
    for pos in range(*edges):
        slices[pos] = map_[str(pos)]
    return slices


def render_map(map_, player_x, player_y, blocks):

    # Sorts the dict as a list by pos
    map_ = list(map_.items())
    map_.sort(key=lambda item: int(item[0]))

    # Seperates the pos and data
    map_ = tuple(zip(*map_))[1]

    # Orientates the data
    map_ = tuple(zip(*map_))

    # Output the map
    out = ''
    for y, row in enumerate(map_):
        for x, pixel in enumerate(row):

            # Add the player
            if x == player_x and y in [player_y, player_y - 1]:
                pixel = '^*'[y - player_y]

            out += blocks[pixel][0]
        out += '\n'

    print(CLS + out, end='')


def slice_height(pos, meta):

    slice_height_ = world_gen['ground_height']

    # Check surrounding slices for a hill
    for x in range(pos - world_gen['max_hill'] * 2,
                   pos + world_gen['max_hill'] * 2):
        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(x) + 'hill')

        # Generate a hill with a 5% chance
        if random.random() <= 0.05:
            # Make top of hill flat
            # Set height to height of hill minus distance from hill
            hill_height = (world_gen['ground_height'] +
                random.randint(0, world_gen['max_hill']) - abs(pos-x)/2)
            hill_height -= 1 if pos == x else 0

            if hill_height > slice_height_:
                slice_height_ = hill_height

    return int(slice_height_)


def add_tree(slice_, pos, meta):
    # Maximum width of half a tree
    max_half_tree = int(len(max(trees, key=lambda tree: len(tree))) / 2)

    for x in range(pos - max_half_tree, pos + max_half_tree + 1):
        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(x) + 'tree')

        # Generate a tree with a 5% chance
        if random.random() <= 0.05:
            tree = random.choice(trees)

            # Get height above ground
            air_height = world_gen['height'] - slice_height(x, meta)

            # Center tree slice (contains trunk)
            center_leaves = tree[int(len(tree)/2)]
            trunk_depth = next(i for i, leaf in enumerate(center_leaves[::-1])
                               if leaf)
            tree_height = random.randint(2, air_height
                          - len(center_leaves) + trunk_depth)

            # Find leaves of current tree
            for i, leaf_slice in enumerate(tree):
                leaf_pos = x + (i - int(len(tree) / 2))
                if leaf_pos == pos:
                    leaf_height = air_height - tree_height - trunk_depth - 1

                    # Add leaves to slice
                    for j, leaf in enumerate(leaf_slice):
                        if leaf:
                            slice_[leaf_height + j] = '@'

            if x == pos:
                # Add trunk to slice
                for i in range(air_height - tree_height,
                               air_height):
                    slice_[i] = '|'

    return slice_


def add_ores(slice_, pos, meta):
    for ore in world_gen['ores'].values():
        for x in range(pos - int(ore['vain_size'] / 2),
                       pos + ceil(ore['vain_size'] / 2)):
            # Set seed for random numbers based on position and ore
            random.seed(str(meta['seed']) + str(x) + ore['char'])

            # Gernerate a ore with a probability
            if random.random() <= ore['chance']:
                root_ore_height = random.randint(ore['lower'], ore['upper'])

                # Generates ore at random position around root ore
                random.seed(str(meta['seed']) + str(pos) + ore['char'])
                ore_height = (root_ore_height +
                              random.randint(-int(ore['vain_size'] / 2),
                                             ceil(ore['vain_size'] / 2)))

                # Won't allow ore above surface
                if 0 < ore_height < slice_height(pos, meta):
                    slice_[world_gen['height'] - ore_height] = ore['char']

    return slice_


def gen_slice(pos, meta):

    slice_height_ = slice_height(pos, meta)

    # Form slice of sky - ground - stone layers
    slice_ = (
        [' '] * (world_gen['height'] - slice_height_) +
        ['-'] +
        ['#'] * (slice_height_ - 1)
    )

    slice_ = add_tree(slice_, pos, meta)
    slice_ = add_ores(slice_, pos, meta)

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


def is_solid(blocks, block):
    return blocks[block][1]


def ground_height(slice_, blocks):
    return next(i for i, block in enumerate(slice_) if blocks[block][1])


def gen_blocks():

    # Block dict entries - (str char, bool solid)
    return {
        ' ': (colorStr(' ', bg=CYAN), False), # Air
        '-': (colorStr('v', bg=GREEN, fg=GREEN, style=DARK), True), # Grass
        '|': (colorStr('#', fg=BLACK, bg=MAGENTA, style=LIGHT), True), # Wood
        '@': (colorStr('@', fg=GREEN, bg=GREEN, style=DARK), True), # Leaves
        '#': (colorStr('~', bg=BLACK, style=CLEAR), True), # Stone
        'x': (colorStr('x', fg=BLACK, bg=BLACK, style=DARK), True), # Coal
        '+': (colorStr('+', fg=RED, bg=BLACK, style=LIGHT), True), # Iron
        ':': (colorStr(':', fg=RED, bg=BLACK, style=DARK), True), # Redstone
        '"': (colorStr('"', fg=YELLOW, bg=BLACK), True), # Gold
        'o': (colorStr('o', fg=BLUE, bg=BLACK, style=LIGHT), True), # Diamond
        'o': (colorStr('o', fg=GREEN, bg=BLACK, style=DARK), True), # Emerald
        '*': (colorStr('*', fg=WHITE, bg=CYAN), True), # Player head
        '^': (colorStr('^', fg=WHITE, bg=CYAN), True) # Player legs
    }
