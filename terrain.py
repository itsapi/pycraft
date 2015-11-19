import random
from collections import OrderedDict
from math import ceil

import render
from data import world_gen


# Maximum width of half a tree
max_half_tree = int(len(max(world_gen['trees'], key=lambda tree: len(tree))) / 2)
EMPTY_SLICE = [' ' for y in range(world_gen['height'])]

get_chunk_list = lambda slice_list: list(set(int(i) // world_gen['chunk_size'] for i in slice_list))

blocks = render.blocks


def move_map(map_, edges):
    # Create subset of slices from map_ between edges
    slices = {}
    for pos in range(*edges):
        slices[pos] = map_[str(pos)]
    return slices


def slice_height(pos, meta):
    slice_height_ = world_gen['ground_height']

    # Check surrounding slices for a hill with min gradient
    for x in range(pos - world_gen['max_hill'] * world_gen['min_grad'],
                   pos + world_gen['max_hill'] * world_gen['min_grad']):
        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(x) + 'hill')

        # Generate a hill with a 5% chance
        if random.random() <= 0.05:

            # Get gradient for left, or right side of hill
            gradient_l = random.randint(1, world_gen['min_grad'])
            gradient_r = random.randint(1, world_gen['min_grad'])

            gradient = gradient_r if x < pos else gradient_l

            # Height is distance from hill with gradient
            d_hill_height = abs(pos-x) / gradient

            # Cut off anything that would not be a part of the hill assuming
            #   flat ground.
            if d_hill_height < world_gen['max_hill']:

                hill_height = (world_gen['ground_height'] +
                    random.randint(0, world_gen['max_hill']) - d_hill_height)
                # Make top of hill flat
                hill_height -= 1 if pos == x else 0

                slice_height_ = max(slice_height_, hill_height)

    return int(slice_height_)


def add_tree(slice_, pos, meta):
    for x in range(pos - max_half_tree, pos + max_half_tree + 1):
        tree_chance = biome(x, meta)

        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(x) + 'tree')

        # Generate a tree with a chance dependent on the biome
        if random.random() <= tree_chance:
            tree = random.choice(world_gen['trees'])

            # Get height above ground
            air_height = world_gen['height'] - slice_height(x, meta)

            # Centre tree slice (contains trunk)
            center_leaves = tree[int(len(tree)/2)]
            trunk_depth = next(i for i, leaf in enumerate(center_leaves[::-1])
                               if leaf)
            tree_height = random.randint(2, air_height
                          - len(center_leaves) + trunk_depth)

            # Find leaves of current tree
            for i, leaf_slice in enumerate(tree):
                leaf_pos = x + (i - int(len(tree) / 2))
                if leaf_pos == pos:
                    leaf_height = air_height - tree_height - (len(leaf_slice) - trunk_depth)

                    # Add leaves to slice
                    for j, leaf in enumerate(leaf_slice):
                        if leaf:
                            sy = leaf_height + j
                            slice_[sy] = spawn_hierarchy(('@', slice_[sy]))

            if x == pos:
                # Add trunk to slice
                for i in range(air_height - tree_height,
                               air_height):
                    slice_[i] = spawn_hierarchy(('|', slice_[i]))

    return slice_


def biome(pos, meta):
    biome_type = []

    # Check surrounding slices for a biome marker
    for biome_x in range(pos - int(world_gen['max_biome_size'] / 2),
                         pos + int(world_gen['max_biome_size'] / 2)):
        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(biome_x) + 'biome')

        # Generate a biome marker with a 5% chance
        if random.random() <= .05:
            biome_type.append(random.choice(world_gen['biome_tree_weights']))

    # If not plains or forest, it's normal
    return max(set(biome_type), key=biome_type.count) if biome_type else .05


def add_ores(slice_, pos, meta, slice_height_):
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
                if ore['lower'] < ore_height < min(ore['upper'], slice_height_):
                    sy = world_gen['height'] - ore_height
                    slice_[sy] = spawn_hierarchy((ore['char'], slice_[sy]))

    return slice_


def add_tall_grass(slice_, pos, meta, slice_height_):
    # Set seed for random numbers based on position and grass
    random.seed(str(meta['seed']) + str(pos) + 'grass')

    # Gernerate a grass with a probability
    if random.random() <= world_gen['tall_grass_rate']:
        sy = world_gen['height'] - slice_height_ - 1
        slice_[sy] = spawn_hierarchy(('v', slice_[sy]))

    return slice_


class Cache(OrderedDict):
    """ Implements a Dict with a size limit.
        Beyond which it replaces the oldest item. """

    def __init__(self, *args, **kwds):
        self._limit = kwds.pop("limit", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_limit()

    def _check_limit(self):
        if self._limit is not None:
            while len(self) > self._limit:
                self.popitem(last=False)


features = Cache(limit=(world_gen['chunk_size'] * 4))  # Magic number!


def gen_features(features, range_, meta):
    """ Ensures the features within `range` exist in `features` """

    for x in range_:
        if features.get(str(x)) is None:

            # Init to empty, so 'no features' is cached.
            features[str(x)] = []

            # Biomes
            random.seed(str(meta['seed']) + str(x) + 'biome')
            if random.random() <= .05:

                attrs = {}
                attrs['tree_chance'] = random.choice(world_gen['biome_tree_weights'])

                if str(x) not in features:
                    features[str(x)] = []

                features[str(x)].append({
                    'type': 'biome',
                    'attrs': attrs
                })

            # Hills
            random.seed(str(meta['seed']) + str(x) + 'hill')
            if random.random() <= 0.05:

                attrs = {}
                attrs['gradient_l'] = random.randint(1, world_gen['min_grad']),
                attrs['gradient_r'] = random.randint(1, world_gen['min_grad']),
                attrs['height'] = random.randint(0, world_gen['max_hill'])

                if str(x) not in features:
                    features[str(x)] = []

                features[str(x)].append({
                    'type': 'hill',
                    'attrs': attrs
                })

            # Trees

            # TODO: `tree_chance` depends on the biome...?
            tree_chance = 0

            random.seed(str(meta['seed']) + str(x) + 'tree')
            if random.random() <= tree_chance:

                attrs = {}
                attrs['type'] = random.choice(world_gen['trees'])

                # Centre tree slice (contains trunk)
                center_leaves = tree[int(len(tree)/2)]
                trunk_depth = next(i for i, leaf in enumerate(center_leaves[::-1]) if leaf)
                attrs['height'] = random.randint(2, air_height - len(center_leaves) + trunk_depth)

                features[str(x)].append({
                    'type': 'tree',
                    'attrs': attrs
                })

            # Ores
            # NOTE: Ores seem to be the way to model the generalisation of the
            #         rest of the features after
            for ore in world_gen['ores'].values():

                random.seed(str(meta['seed']) + str(x) + ore['char'])
                if random.random() <= ore['chance']:

                    attrs = {}
                    attrs['type'] = ore['char']
                    attrs['ore_root_height'] = random.randint(ore['lower'], ore['upper'])

                    features[str(x)].append({
                        'type': 'ore_root',
                        'attrs': attrs
                    })

            # TODO: Grass?


def gen_chunk(chunk_pos, meta):
    # First generate all the features we will need
    #   for all the slice is in this chunk,

    MAX_FEATURE_RANGE = 0  # TODO: Temp!

    feature_range = (chunk_pos - MAX_FEATURE_RANGE,
                     chunk_pos + world_gen['chunk_size'] + MAX_FEATURE_RANGE)
    gen_features(features, feature_range, meta)

    chunk = {}
    for d_pos in range(world_gen['chunk_size']):
        pos = (chunk_pos * world_gen['chunk_size']) + d_pos

        chunk.update({str(pos): gen_slice(pos, meta)})

    return chunk


def gen_slice(pos, meta):
    slice_height_ = slice_height(pos, meta)

    # Form slice of sky, grass, stone, bedrock
    slice_ = (
        [' '] * (world_gen['height'] - slice_height_) +
        ['-'] +
        ['#'] * (slice_height_ - 2) + # 2 for grass and bedrock
        ['_']
    )

    # TODO: Combine loops in each of these functions?
    slice_ = add_tree(slice_, pos, meta)
    slice_ = add_ores(slice_, pos, meta, slice_height_)
    slice_ = add_tall_grass(slice_, pos, meta, slice_height_)

    return slice_


def detect_edges(map_, edges):
    slices = []
    for pos in range(*edges):
        if not str(pos) in map_:
            slices.append(pos)

    return slices


def spawn_hierarchy(tests):
    return max(tests, key=lambda block: blocks[block]['hierarchy'])


def is_solid(block):
    return blocks[block]['solid']


def ground_height(slice_):
    return next(i for i, block in enumerate(slice_) if blocks[block]['solid'])
