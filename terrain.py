import random
from collections import OrderedDict
from math import ceil

import render
from data import world_gen
from console import log


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
    for x in range(pos - MAX_HALF_TREE, pos + MAX_HALF_TREE + 1):
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
        # if random.random() <= .05:
        #     biome_type.append(random.choice(world_gen['biome_tree_weights']))

    # If not plains or forest, it's normal
    return max(set(biome_type), key=biome_type.count) if biome_type else .05


def add_ores(slice_, pos, meta, slice_height_):
    for ore in world_gen['ores'].values():
        for x in range(pos - int(ore['vain_size'] / 2),
                       pos + ceil(ore['vain_size'] / 2)):
            # Set seed for random numbers based on position and ore
            random.seed(str(meta['seed']) + str(x) + ore['char'])

            # Generate an ore with a probability
            if random.random() <= ore['chance']:
                root_ore_height = random.randint(ore['lower'], ore['upper'])

                # TODO: Use this for vain gen!
                """
                    # Generates ore at random position around root ore
                    # TODO: Do we need a `vain_density` value per ore type?

                    pot_vain_blocks = ore['vain_size'] ** 2
                    # The bits describe the shape of the vain,
                    #   top to bottom, left to right.
                    vain_shape = random.getkrandbits(pot_vain_blocks)
                    this_ores = vain_shape[]
                """

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

    # Generate a grass with a probability
    if random.random() <= world_gen['tall_grass_rate']:
        sy = world_gen['height'] - slice_height_ - 1
        slice_[sy] = spawn_hierarchy(('v', slice_[sy]))

    return slice_


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
                    # TODO: Do we need a `vain_density` value per ore type?
                    pot_vain_blocks = ore['vain_size'] ** 2

                    # The bits describe the shape of the vain,
                    #   top to bottom, left to right.
                    attrs['vain_shape'] = random.getrandbits(pot_vain_blocks)

                    features['slices'][str(x)][feature_name] = attrs


def gen_chunk(chunk_n, meta):
    chunk_pos = chunk_n * world_gen['chunk_size']

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

    trees_gen = 0

    # Insert trees and ores
    for feature_x, slice_features in features['slices'].items():
        feature_x = int(feature_x)

        # Tree
        if slice_features.get('tree'):
            tree = slice_features['tree']
            leaves = world_gen['trees'][tree['type']]
            half_leaves = int(len(leaves) / 2)

            for leaf_dx, leaf_slice in enumerate(leaves):
                leaf_x = feature_x + (leaf_dx - half_leaves)

                if chunk_pos <= leaf_x < chunk_pos + world_gen['chunk_size']:
                    air_height = world_gen['height'] - ground_heights[str(feature_x)]
                    leaf_height = air_height - tree['height'] - len(leaf_slice) + tree['trunk_depth']

                    # Add leaves to slice
                    for leaf_dy, leaf in enumerate(leaf_slice):
                        if leaf:
                            leaf_y = leaf_height + leaf_dy
                            chunk[str(leaf_x)][leaf_y] = spawn_hierarchy(('@', chunk[str(leaf_x)][leaf_y]))

            # Add trunk if in chunk
            if chunk_pos <= feature_x < chunk_pos + world_gen['chunk_size']:
                trees_gen += 1
                air_height = world_gen['height'] - ground_heights[str(feature_x)]
                for trunk_y in range(air_height - tree['height'], air_height):
                    chunk[str(feature_x)][trunk_y] = spawn_hierarchy(('|', chunk[str(feature_x)][trunk_y]))

        # All ores
        for name, ore in world_gen['ores'].items():
            feature_name = name + '_ore_root'

            if slice_features.get(feature_name):
                ore_feature = slice_features[feature_name]

                for block_pos in range(ore['vain_size'] ** 2):
                    if ore_feature['vain_shape'] & (1 << block_pos):

                        # Centre on root ore
                        block_dx = (block_pos % ore['vain_size']) - int((ore['vain_size'] - 1) / 2)
                        block_dy = int(block_pos / ore['vain_size']) - int((ore['vain_size'] - 1) / 2)

                        block_x = block_dx + feature_x
                        block_y = block_dy + ore_feature['root_height']

                        # Won't allow ore above surface
                        if chunk_pos <= block_x < chunk_pos + world_gen['chunk_size']:
                            if world_gen['height'] > block_y > world_gen['height'] - ground_heights[str(block_x)]:
                                chunk[str(block_x)][block_y] = spawn_hierarchy((ore['char'], chunk[str(block_x)][block_y]))

    log('trees gen:', trees_gen, m=1)

    return chunk


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
