import random
from collections import OrderedDict
from math import ceil

import render
from data import world_gen
from console import log, DEBUG


# Maximum width of half a tree
# TODO: Do the two half ranges like ores
MAX_HALF_TREE = int(len(max(world_gen['trees'], key=lambda tree: len(tree))) / 2)

largest_ore = max(map(lambda ore: world_gen['ores'][ore]['vain_size'], world_gen['ores']))
MAX_ORE_RANGE = (int((largest_ore - 1) / 2), (int(largest_ore / 2) + 1))

EMPTY_SLICE = [' ' for y in range(world_gen['height'])]

get_chunk_list = lambda slice_list: list(set(int(i) // world_gen['chunk_size'] for i in slice_list))

blocks = render.blocks


def move_map(map_, edges):
    # Create subset of slices from map_ between edges
    slices = {}
    for pos in range(*edges):
        slices[pos] = map_[str(pos)]
    return slices


def detect_edges(map_, edges):
    slices = []
    for pos in range(*edges):
        if not str(pos) in map_:
            slices.append(pos)

    return slices


def spawn_hierarchy(tests):
    # TODO: Use argument expansion for tests
    return max(tests, key=lambda block: blocks[block]['hierarchy'])


def is_solid(block):
    return blocks[block]['solid']


def ground_height(slice_):
    return next(i for i, block in enumerate(slice_) if blocks[block]['solid'])


class TerrainCache(OrderedDict):
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


# TODO: This probably shouldn't stay here...
features = {}
def init_features():
    global features
    cache_size = 2 * ((world_gen['max_hill'] * world_gen['min_grad'] * 2) + world_gen['chunk_size'])
    features = {
        'chunks': TerrainCache(limit=(cache_size // world_gen['chunk_size']) + 1),
        'slices': TerrainCache(limit=cache_size)
    }

init_features()


# # TODO: Use this for the other functions!
# def gen_features(generator, features, feature_group_name, chunk_pos, meta):
#     """ Ensures the features within `range` exist in `features` """

#     feature_cache = features[feature_group_name]

#     for x in range(chunk_pos - RAD, chunk_pos + world_gen['chunk_size'] + RAD):
#         if feature_cache.get(str(chunk_pos)) is None:

#             # Init to empty, so 'no features' is cached.
#             feature_cache[str(chunk_pos)] = {}

#             random.seed(str(meta['seed']) + str(chunk_pos) + feature_group_name)
#             feature_cache[str(chunk_pos)]['biome'] = generator()


def gen_biome_features(features, chunk_pos, meta):
    # TODO: Each of these `if` blocks should be abstracted into a function
    #         which just returns the `attrs` object.

    if features['chunks'].get(str(chunk_pos)) is None:
        # Init to empty, so 'no features' is cached.
        features['chunks'][str(chunk_pos)] = {}

    # If it is not None, it has all ready been generated.
    if features['chunks'][str(chunk_pos)].get('biome') is None:

        # TODO: ATM using basic per chunk biomes, see #71
        random.seed(str(meta['seed']) + str(chunk_pos) + 'biome')

        biomes_population = []
        for name, data in world_gen['biomes'].items():
            biomes_population.extend([name] * int(data['chance'] * 100))

        attrs = {}
        attrs['type'] = random.choice(sorted(biomes_population))

        features['chunks'][str(chunk_pos)]['biome'] = attrs


def gen_hill_features(features, chunk_pos, meta):
    max_hill_rad = world_gen['max_hill'] * world_gen['min_grad']

    for x in range(chunk_pos - max_hill_rad,
                   chunk_pos + world_gen['chunk_size'] + max_hill_rad):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features['slices'].get(str(x)) is None:
            # Init to empty, so 'no features' is cached.
            features['slices'][str(x)] = {}

        # If it is not None, it has all ready been generated.
        if features['slices'][str(x)].get('hill') is None:

            random.seed(str(meta['seed']) + str(x) + 'hill')
            if random.random() <= 0.05:

                attrs = {}
                attrs['gradient_l'] = random.randint(1, world_gen['min_grad'])
                attrs['gradient_r'] = random.randint(1, world_gen['min_grad'])
                attrs['height'] = random.randint(0, world_gen['max_hill'])

                features['slices'][str(x)]['hill'] = attrs


def gen_tree_features(features, ground_heights, chunk_pos, meta):
    current_chunk_biome = features['chunks'][str(chunk_pos)]['biome']['type']
    log(current_chunk_biome, m=1)

    for x in range(chunk_pos - MAX_HALF_TREE, chunk_pos + world_gen['chunk_size'] + MAX_HALF_TREE):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features['slices'].get(str(x)) is None:
            # Init to empty, so 'no features' is cached.
            features['slices'][str(x)] = {}

        # If it is not None, it has all ready been generated.
        if features['slices'][str(x)].get('tree') is None:

            random.seed(str(meta['seed']) + str(x) + 'tree')
            tree_chance = world_gen['biomes'][current_chunk_biome]['trees']
            if random.random() <= tree_chance:

                attrs = {}
                attrs['type'] = random.randint(0, len(world_gen['trees'])-1)

                # Centre tree slice (contains trunk)
                # TODO: This calculation could be done on start-up, and stored
                #         with each tree type.
                tree = world_gen['trees'][attrs['type']]
                center_leaves = tree[int(len(tree) / 2)]
                attrs['trunk_depth'] = next(i for i, leaf in enumerate(center_leaves[::-1]) if leaf)

                # Get space above ground
                air_height = world_gen['height'] - ground_heights[str(x)]
                attrs['height'] = random.randint(2, air_height - len(center_leaves) + attrs['trunk_depth'])

                features['slices'][str(x)]['tree'] = attrs


def gen_ore_features(features, ground_heights, chunk_pos, meta):
    for x in range(chunk_pos - MAX_ORE_RANGE[0], chunk_pos + world_gen['chunk_size'] + MAX_ORE_RANGE[1]):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features['slices'].get(str(x)) is None:
            # Init to empty, so 'no features' is cached.
            features['slices'][str(x)] = {}

        # Ores
        # NOTE: Ores seem to be the way to model the generalisation of the
        #         rest of the features after
        for name, ore in world_gen['ores'].items():
            feature_name = name + '_ore_root'

            # If it is not None, it has all ready been generated.
            if features['slices'][str(x)].get(feature_name) is None:

                random.seed(str(meta['seed']) + str(x) + feature_name)
                if random.random() <= ore['chance']:

                    attrs = {}
                    attrs['root_height'] = world_gen['height'] - random.randint(
                        ore['lower'],
                        min(ore['upper'], (ground_heights[str(x)] - 1))  # -1 for grass.
                    )

                    # Generates ore at random position around root ore
                    pot_vain_blocks = ore['vain_size'] ** 2

                    # Describes the shape of the vain,
                    #   top to bottom, left to right.
                    attrs['vain_shape'] = [b / 100 for b in random.sample(range(0, 100), pot_vain_blocks)]

                    features['slices'][str(x)][feature_name] = attrs


def gen_grass_features(features, ground_heights, chunk_pos, meta):
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features['slices'].get(str(x)) is None:
            # Init to empty, so 'no features' is cached.
            features['slices'][str(x)] = {}

        # If it is not None, it has all ready been generated.
        if features['slices'][str(x)].get('grass') is None:

            random.seed(str(meta['seed']) + str(x) + 'grass')
            if random.random() <= world_gen['tall_grass_rate']:

                attrs = {}
                attrs['y'] = ground_heights[str(x)]

                features['slices'][str(x)]['grass'] = attrs


def in_chunk(pos, chunk_pos):
    return chunk_pos <= pos < chunk_pos + world_gen['chunk_size']


def build_tree(chunk, chunk_pos, x, tree_feature, ground_heights):
    """ Adds a tree feature at x to the chunk. """

    # Add trunk
    if in_chunk(x, chunk_pos):
        air_height = world_gen['height'] - ground_heights[str(x)]
        for trunk_y in range(air_height - tree_feature['height'], air_height - (DEBUG * 3)):
            chunk[str(x)][trunk_y] = spawn_hierarchy(('|', chunk[str(x)][trunk_y]))

    # Add leaves
    leaves = world_gen['trees'][tree_feature['type']]
    half_leaves = int(len(leaves) / 2)

    for leaf_dx, leaf_slice in enumerate(leaves):
        leaf_x = x + (leaf_dx - half_leaves)

        if in_chunk(leaf_x, chunk_pos):
            air_height = world_gen['height'] - ground_heights[str(x)]
            leaf_height = air_height - tree_feature['height'] - len(leaf_slice) + tree_feature['trunk_depth']

            for leaf_dy, leaf in enumerate(leaf_slice):
                if leaf:
                    leaf_y = leaf_height + leaf_dy
                    chunk[str(leaf_x)][leaf_y] = spawn_hierarchy(('@', chunk[str(leaf_x)][leaf_y]))


def build_grass(chunk, chunk_pos, x, grass_feature, ground_heights):
    """ Adds a grass feature at x to the chunk. """

    if in_chunk(x, chunk_pos):
        grass_y = world_gen['height'] - ground_heights[str(x)] - 1
        chunk[str(x)][grass_y] = spawn_hierarchy(('v', chunk[str(x)][grass_y]))


def build_ore(chunk, chunk_pos, x, ore_feature, ore, ground_heights):
    """ Adds an ore feature at x to the chunk. """

    for block_pos in range(ore['vain_size'] ** 2):
        if ore_feature['vain_shape'][block_pos] < ore['vain_density']:

            # Centre on root ore
            block_dx = (block_pos % ore['vain_size']) - int((ore['vain_size'] - 1) / 2)
            block_dy = int(block_pos / ore['vain_size']) - int((ore['vain_size'] - 1) / 2)

            block_x = block_dx + x
            block_y = block_dy + ore_feature['root_height']

            if in_chunk(block_x, chunk_pos):
                # Won't allow ore above surface
                if world_gen['height'] > block_y > world_gen['height'] - ground_heights[str(block_x)]:
                    chunk[str(block_x)][block_y] = spawn_hierarchy((ore['char'], chunk[str(block_x)][block_y]))


def gen_chunk(chunk_n, meta):
    chunk_pos = chunk_n * world_gen['chunk_size']

    # TODO: Allow more than one feature per x in features?

    # First generate all the features we will need
    #   for all the slice is in this chunk

    gen_biome_features(features, chunk_pos, meta)
    gen_hill_features(features, chunk_pos, meta)

    # Insert hills because the trees and ores depend on the ground height.
    ground_heights = {}
    for feature_x, slice_features in features['slices'].items():
        feature_x = int(feature_x)

        if slice_features.get('hill'):
            hill = slice_features['hill']

            for d_x in range(-hill['height'] * hill['gradient_l'],
                             hill['height'] * hill['gradient_r']):
                abs_pos = feature_x + d_x

                gradient = hill['gradient_l'] if d_x < 0 else hill['gradient_r']
                hill_height = int(hill['height'] - (abs(d_x) / gradient))

                if d_x == 0:
                    hill_height -= 1

                ground_height = world_gen['ground_height'] + hill_height

                old_height = ground_heights.get(str(abs_pos), 0)
                ground_heights[str(abs_pos)] = max(ground_height, old_height)

    # We have to generate the ground heights before we can calculate the
    #   features which depend on them

    gen_tree_features(features, ground_heights, chunk_pos, meta)
    gen_ore_features(features, ground_heights, chunk_pos, meta)
    gen_grass_features(features, ground_heights, chunk_pos, meta)

    log('chunk_pos', chunk_pos, m=1)
    tree_features = list(filter(lambda f: f[1].get('tree'), features['slices'].items()))
    log('trees in cache\n', [str(f[0]) for f in tree_features], m=1, trunc=0)
    log('trees in range', [str(f[0]) for f in tree_features if (chunk_pos <= int(f[0]) < chunk_pos + world_gen['chunk_size'])], m=1, trunc=0)

    # Build slices
    chunk = {}
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):
        # Add missing ground heights
        ground_heights.setdefault(str(x), world_gen['ground_height'])

        # Form slice of sky, grass, stone, bedrock
        chunk[str(x)] = (
            [' '] * (world_gen['height'] - ground_heights[str(x)]) +
            ['-'] +
            ['#'] * (ground_heights[str(x)] - 2) +  # 2 for grass and bedrock
            ['_']
        )

    # Insert trees and ores
    for feature_x, slice_features in features['slices'].items():
        feature_x = int(feature_x)

        for feature_name, feature in slice_features.items():

            if feature_name == 'tree':
                build_tree(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'grass':
                build_grass(chunk, chunk_pos, feature_x, feature, ground_heights)

            else:
                for name, ore in world_gen['ores'].items():
                    ore_name = name + '_ore_root'

                    if feature_name == ore_name:
                        build_ore(chunk, chunk_pos, feature_x, feature, ore, ground_heights)
                        break

    return chunk
