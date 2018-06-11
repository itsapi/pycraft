import random
from collections import OrderedDict
from math import ceil, cos, sin, radians, atan2

from data import world_gen, blocks
from console import log, DEBUG


# Maximum width of half a tree
MAX_HALF_TREE = int(len(max(world_gen['trees'], key=lambda tree: len(tree))) / 2)

largest_ore = max(map(lambda ore: world_gen['ores'][ore]['vain_size'], world_gen['ores']))
MAX_ORE_RANGE = (int((largest_ore - 1) / 2), (int(largest_ore / 2) + 1))

EMPTY_SLICE = [' ' for y in range(world_gen['height'])]

get_chunk_list = lambda slice_list: list(set(int(i) // world_gen['chunk_size'] for i in slice_list))

MAX_HILL_RAD = world_gen['max_hill'] * world_gen['min_grad']
MAX_HILL_CHUNKS = ceil(MAX_HILL_RAD / world_gen['chunk_size'])

MAX_BIOME_RAD = world_gen['max_biome']
MAX_BIOME_CHUNKS = ceil(MAX_BIOME_RAD / world_gen['chunk_size'])

flatten = lambda l: [item for sublist in l for item in sublist]
biomes_population = sorted(flatten([name] * int(data['chance'] * 100) for name, data in world_gen['biomes'].items()))


def move_map(map_, edges):
    # Create subset of slices from map_ between edges
    slices = {}
    for pos in range(*edges):
        slices[pos] = map_[pos]
    return slices


def detect_edges(map_, edges):
    slices = []
    for pos in range(*edges):
        if not pos in map_:
            slices.append(pos)

    return slices


def apply_gravity(map_, edges):
    start_pos = (sum(edges) / 2,
                 world_gen['height'] - 1)

    new_blocks = {}
    connected_to_ground = explore_map(map_, edges, start_pos, set())

    for x, slice_ in map_.items():
        if x not in range(*edges):
            continue
        for y in range(len(slice_)-3, -1, -1):
            block = slice_[y]
            if (is_solid(block) and (x, y) not in connected_to_ground):
                new_blocks.setdefault(x, {})
                new_blocks[x][y] = ' '
                new_blocks[x][y+1] = block

    return new_blocks


def explore_map(map_, edges, start_pos, connected_to_ground):
    blocks_to_explore = set([start_pos])
    visted_blocks = set()

    while blocks_to_explore:
        current_pos = blocks_to_explore.pop()
        visted_blocks.add(current_pos)

        if (current_pos[1] >= 0 and current_pos[1] < world_gen['height'] and
                current_pos not in connected_to_ground and
                current_pos[0] in range(edges[0]-1, edges[1]+1)):

            try:
                current_block = map_[current_pos[0]][current_pos[1]]
            except (IndexError, KeyError):
                current_block = None

            if (current_block is not None and
                    is_solid(current_block)) or current_pos[0] in (edges[0]-1, edges[1]):

                connected_to_ground.add(current_pos)
                for (dx, dy) in ((x, y) for x in (-1, 0, 1) for y in (-1, 0, 1)):
                    pos = (current_pos[0] + dx, current_pos[1] + dy)

                    if pos not in visted_blocks:
                        blocks_to_explore.add(pos)

    return connected_to_ground


def spawn_hierarchy(tests):
    # TODO: Use argument expansion for tests
    return max(tests, key=lambda block: blocks[block]['hierarchy'])


def is_solid(block):
    return blocks[block]['solid']


def in_chunk(pos, chunk_pos):
    return chunk_pos <= pos < chunk_pos + world_gen['chunk_size']


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


features = TerrainCache(limit=(world_gen['max_biome'] * 4) + world_gen['chunk_size'])


# # TODO: Use this for the other functions!
# def gen_features(generator, features, feature_group_name, chunk_pos, meta):
#     """ Ensures the features within `range` exist in `features` """

#     feature_cache = features[feature_group_name]

#     for x in range(chunk_pos - RAD, chunk_pos + world_gen['chunk_size'] + RAD):
#         if feature_cache.get(chunk_pos) is None:

#             # Init to empty, so 'no features' is cached.
#             feature_cache[chunk_pos] = {}

#             random.seed(str(meta['seed']) + str(chunk_pos) + feature_group_name)
#             feature_cache[chunk_pos]['biome'] = generator()


def gen_biome_chunk_features(chunk_pos, chunk_features, seed):
    chunk_biomes = []
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        if random.random() <= 0.05:

            slice_biome = {}
            slice_biome['x'] = x
            slice_biome['type'] = random.choice(biomes_population)
            slice_biome['radius'] = random.randint(world_gen['min_biome'], world_gen['max_biome'])

            features[x]['biome'] = slice_biome

            chunk_biomes.append(slice_biome)

    return chunk_biomes


def gen_hill_chunk_features(chunk_pos, chunk_features, seed):
    chunk_hills = []
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        if random.random() <= 0.05:

            slice_hill = {}
            slice_hill['x'] = x
            slice_hill['gradient_l'] = random.randint(1, world_gen['min_grad'])
            slice_hill['gradient_r'] = random.randint(1, world_gen['min_grad'])
            slice_hill['height'] = random.randint(0, world_gen['max_hill'])

            chunk_hills.append(slice_hill)

    return chunk_hills


def gen_biome_slice_features(x, chunk_features, slice_features, seed):

    slice_biome = ('normal', None)

    if chunk_features.get('biomes') is not None:
        for biome in chunk_features.get('biomes'):
            slice_biome = (biome['type'], biome['x'])

    return slice_biome


def gen_ground_height_slice_features(x, chunk_features, slice_features, seed):

    ground_height = world_gen['ground_height']

    if chunk_features.get('hills') is not None:
        for hill in chunk_features.get('hills'):
            hill_dist = x - hill['x']

            if hill_dist == 0:
                gradient = 1
            elif hill_dist > 0:
                gradient = hill['gradient_r']
            else:
                gradient = hill['gradient_l']

            hill_height = int(hill['height'] - (abs(hill_dist) / gradient))
            new_ground_height = world_gen['ground_height'] + hill_height

            ground_height = max(ground_height, new_ground_height)

    return ground_height


def gen_tree_features(x, chunk_features, slice_features, seed):

    biome = features[x].get('slice_biome')
    ground_height = features[x].get('ground_height')

    biome_data = world_gen['biomes'][biome[0]]
    boime_tree_chance = biome_data['trees']

    tree_type = random.randint(0, len(world_gen['trees'])-1)
    tree_data = world_gen['trees'][tree_type]

    tree_chance = boime_tree_chance * tree_data['chance']

    if random.random() <= tree_chance:

        tree_feature = {}
        tree_feature['type'] = tree_type

        leaves = tree_data['leaves']

        # Centre tree slice (contains trunk)
        # TODO: This calculation could be done on start-up, and stored
        #         with each tree type.
        center_leaves = leaves[int(len(leaves) / 2)]
        if 1 in center_leaves:
            tree_feature['trunk_depth'] = center_leaves[::-1].index(1)
        else:
            tree_feature['trunk_depth'] = len(center_leaves)

        # Get space above ground
        air_height = world_gen['height'] - ground_height
        tree_height = air_height - (len(center_leaves) - tree_feature['trunk_depth'])
        tree_height = min(tree_height, tree_data['min_height'])

        tree_feature['height'] = random.randint(tree_data['min_height'], max(tree_height, 2))

        return tree_feature


def gen_ore_features(x, chunk_features, slice_features, seed):

    biome = features[x].get('slice_biome')
    ground_height = features[x].get('ground_height')

    ore_features = {}

    for ore_name, ore in world_gen['ores'].items():

        random.seed(seed + ore_name)
        if random.random() <= ore['chance']:

            upper = int(world_gen['height'] * ore['upper'])
            lower = int(world_gen['height'] * ore['lower'])

            ore_feature = {}
            ore_feature['root_height'] = world_gen['height'] - random.randint(
                lower, min(upper, (ground_height - 1))  # -1 for grass.
            )

            # Generates ore at random position around root ore
            pot_vain_blocks = ore['vain_size'] ** 2

            # Describes the shape of the vain,
            #   top to bottom, left to right.
            ore_feature['vain_shape'] = [b / 100 for b in random.sample(range(0, 100), pot_vain_blocks)]

            ore_features[ore_name] = ore_feature

    return ore_features


def gen_grass_features(x, chunk_features, slice_features, seed):

    biome = features[x].get('slice_biome')
    ground_height = features[x].get('ground_height')

    biome_data = world_gen['biomes'][biome[0]]
    grass_chance = biome_data['grass']

    if random.random() <= grass_chance:

        grass_feature = {}
        grass_feature['y'] = ground_height

        return grass_feature


def gen_cave_features(features, ground_heights, slices_biome, chunk_pos, meta):

    cave_y_res = 2  # Double the y resolution of the CA to correct for aspect ratio
    ca_iterations = 6

    air_points = set()
    air_points_x_min = chunk_pos - ca_iterations
    air_points_x_max = chunk_pos + world_gen['chunk_size'] + ca_iterations

    for x in range(air_points_x_min, air_points_x_max):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('cave_initial_air_points') is None:
            random.seed(str(meta['seed']) + str(x) + 'cave')

            # Generate air points for this slice
            slice_air_points = set()
            for y in range(cave_y_res * (ground_heights[x] - 2)):
                world_y = world_gen['height'] - (y/cave_y_res) - 2

                if random.random() < world_gen['cave_chance']:
                    slice_air_points.add((x, world_y))

            if slice_air_points:
                features[x]['cave_initial_air_points'] = slice_air_points

        # Store slice air points in our local collection of air points for CA generation
        if features[x].get('cave_initial_air_points'):
            air_points = air_points.union(features[x]['cave_initial_air_points'])

    if features[chunk_pos].get('cave') is None:
        # Perform cellular automata
        for i in range(ca_iterations):
            new_air_points = set()

            for x in range(air_points_x_min, air_points_x_max):
                for y in range(cave_y_res * (ground_heights[x] - 2)):
                    world_y = world_gen['height'] - (y/cave_y_res) - 2

                    n_neighbours = 0
                    for dx in (-1, 0, 1):
                        for dy in (-(1/cave_y_res), 0, (1/cave_y_res)):
                            if (x + dx, world_y + dy) in air_points:
                                n_neighbours += 1

                    if n_neighbours < 5:
                        new_air_points.add((x, world_y))

            air_points = new_air_points

        features[chunk_pos]['cave'] = air_points



def build_tree(chunk, chunk_pos, x, tree_feature, ground_heights):
    """ Adds a tree feature at x to the chunk. """

    # Add trunk
    if in_chunk(x, chunk_pos):
        air_height = world_gen['height'] - ground_heights[x]
        for trunk_y in range(air_height - tree_feature['height'], air_height - (bool(DEBUG) * 3)):
            chunk[x][trunk_y] = spawn_hierarchy(('|', chunk[x][trunk_y]))

    # Add leaves
    leaves = world_gen['trees'][tree_feature['type']]['leaves']
    half_leaves = int(len(leaves) / 2)

    for leaf_dx, leaf_slice in enumerate(leaves):
        leaf_x = x + (leaf_dx - half_leaves)

        if in_chunk(leaf_x, chunk_pos):
            air_height = world_gen['height'] - ground_heights[x]
            leaf_height = air_height - tree_feature['height'] - len(leaf_slice) + tree_feature['trunk_depth']

            for leaf_dy, leaf in enumerate(leaf_slice):
                if (bool(DEBUG) and leaf_dy == 0) or (not bool(DEBUG) and leaf):
                    leaf_y = leaf_height + leaf_dy
                    chunk[leaf_x][leaf_y] = spawn_hierarchy(('@', chunk[leaf_x][leaf_y]))


def build_grass(chunk, chunk_pos, x, grass_feature, ground_heights):
    """ Adds a grass feature at x to the chunk. """

    if in_chunk(x, chunk_pos):
        grass_y = world_gen['height'] - ground_heights[x] - 1
        chunk[x][grass_y] = spawn_hierarchy(('v', chunk[x][grass_y]))


def build_ore(chunk, chunk_pos, x, ore_feature, ore, ground_heights):
    """ Adds an ore feature at x to the chunk. """

    for block_pos in range(ore['vain_size'] ** 2):
        if ore_feature['vain_shape'][block_pos] < ore['vain_density']:

            # Centre on root ore
            block_dx = (block_pos % ore['vain_size']) - int((ore['vain_size'] - 1) / 2)
            block_dy = int(block_pos / ore['vain_size']) - int((ore['vain_size'] - 1) / 2)

            block_x = block_dx + x
            block_y = block_dy + ore_feature['root_height']

            if not in_chunk(block_x, chunk_pos):
                continue

            if not world_gen['height'] > block_y > world_gen['height'] - ground_heights[block_x]:
                continue

            if chunk[block_x][block_y] is ' ':
                continue

            chunk[block_x][block_y] = spawn_hierarchy((ore['char'], chunk[block_x][block_y]))


def build_cave(chunk, chunk_pos, x, cave_feature, ground_heights):
    """ Adds caves at x to the chunk. """

    for (world_x, y) in cave_feature:
        if in_chunk(world_x, chunk_pos):
            chunk[world_x][int(y)] = ' '


def generate_slice_features(features, chunk_pos, meta, feature_generator, feature_name, feature_buffer):
    for x in range(chunk_pos - feature_buffer[0], chunk_pos + world_gen['chunk_size'] + feature_buffer[1]):

        slice_chunk_pos = (x // world_gen['chunk_size']) * world_gen['chunk_size']

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get(feature_name) is None:

            seed = str(meta['seed']) + str(x) + feature_name
            random.seed(seed)

            features[x][feature_name] = feature_generator(x, features[slice_chunk_pos], features[x], seed)


def generate_chunk_features(features, chunk_n, meta, feature_generator, feature_name, feature_buffer):
    for chunk_n_gen in range(chunk_n - feature_buffer[0], chunk_n + feature_buffer[1]):
        chunk_pos = chunk_n_gen * world_gen['chunk_size']

        if features.get(chunk_pos) is None:
            # Init to empty, so 'no features' is cached.
            features[chunk_pos] = {}

        # If it is not None, it has all ready been generated.
        if features[chunk_pos].get(feature_name) is None:

            seed = str(meta['seed']) + str(chunk_pos) + feature_name
            random.seed(seed)

            features[chunk_pos][feature_name] = feature_generator(chunk_pos, features[chunk_pos], seed)


def gen_chunk(chunk_n, meta):
    chunk_pos = chunk_n * world_gen['chunk_size']

    # TODO: Allow more than one feature per x in features?

    # First generate all the features we will need
    #   for all the slice is in this chunk

    generate_chunk_features(features, chunk_n, meta, gen_hill_chunk_features, 'hills', (MAX_HILL_CHUNKS, MAX_HILL_CHUNKS))
    generate_slice_features(features, chunk_pos, meta, gen_ground_height_slice_features, 'ground_height', (MAX_HILL_RAD, MAX_HILL_RAD))

    generate_chunk_features(features, chunk_n, meta, gen_biome_chunk_features, 'biomes', (MAX_BIOME_CHUNKS, MAX_BIOME_CHUNKS))
    generate_slice_features(features, chunk_pos, meta, gen_biome_slice_features, 'slice_biome', (MAX_BIOME_RAD, MAX_BIOME_RAD))

    ground_heights = {x: features[x].get('ground_height') for x in range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD)}
    slices_biome = {x: features[x].get('slice_biome') for x in range(chunk_pos - MAX_BIOME_RAD, chunk_pos + world_gen['chunk_size'] + MAX_BIOME_RAD)}

    int_x = list(map(int, ground_heights.keys()))
    log('chunk', chunk_pos, m=1)
    log('max', max(int_x), m=1)
    log('min', min(int_x), m=1)
    log('gh diff', set(range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD)) - set(int_x), m=1, trunc=False)
    log('slices_biome', list(filter(lambda slice_: (int(slice_[0])%16 == 0) or (int(slice_[0])+1)%16 == 0, sorted(slices_biome.items()))), m=1, trunc=False)

    gen_cave_features(features, ground_heights, slices_biome, chunk_pos, meta)

    generate_slice_features(features, chunk_pos, meta, gen_tree_features, 'tree', (MAX_HALF_TREE, MAX_HALF_TREE))
    generate_slice_features(features, chunk_pos, meta, gen_grass_features, 'grass', (0, 0))
    generate_slice_features(features, chunk_pos, meta, gen_ore_features, 'ores', MAX_ORE_RANGE)

    log('chunk_pos', chunk_pos, m=1)
    tree_features = list(filter(lambda f: f[1].get('tree'), features.items()))
    log('trees in cache\n', [str(f[0]) for f in tree_features], m=1, trunc=0)
    log('trees in range', [str(f[0]) for f in tree_features if (chunk_pos <= int(f[0]) < chunk_pos + world_gen['chunk_size'])], m=1, trunc=0)

    chunk = {}
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):
        chunk[x] = (
            [' '] * (world_gen['height'] - ground_heights[x]) +
            ['-'] +
            ['#'] * (ground_heights[x] - 2) +  # 2 for grass and bedrock
            ['_']
        )

    # Insert trees and ores
    for feature_x, slice_features in features.items():
        feature_x = int(feature_x)

        for feature_name, feature in slice_features.items():

            if feature is None:
                continue

            if feature_name == 'tree':
                build_tree(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'grass':
                build_grass(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'cave':
                build_cave(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'ores':
                for ore_name, ore_feature in feature.items():
                    build_ore(chunk, chunk_pos, feature_x, ore_feature, world_gen['ores'][ore_name], ground_heights)


    return chunk, {x: ground_heights[x] for x in range(chunk_pos, chunk_pos+world_gen['chunk_size'])}
