import random, math
from collections import OrderedDict
from math import ceil, cos, sin, radians, atan2

from data import world_gen, blocks
from console import log, DEBUG


MAX_HALF_TREE = int(len(max(world_gen['trees'], key=lambda tree: len(tree))) / 2)

largest_ore = max(map(lambda ore: world_gen['ores'][ore]['vain_size'], world_gen['ores']))
MAX_ORE_RANGE = (int((largest_ore - 1) / 2), (int(largest_ore / 2) + 1))

MAX_HILL_RAD = world_gen['max_hill'] * world_gen['min_grad']
MAX_HILL_CHUNKS = ceil(MAX_HILL_RAD / world_gen['chunk_size'])

MAX_BIOME_RAD = world_gen['max_biome']
MAX_BIOME_CHUNKS = ceil(MAX_BIOME_RAD / world_gen['chunk_size'])

flatten = lambda l: [item for sublist in l for item in sublist]
biomes_population = sorted(flatten([name] * int(data['chance'] * 100) for name, data in world_gen['biomes'].items()))


class TerrainCache(OrderedDict):
    """ Implements a Dict with a size limit.
        Beyond which it replaces the oldest item. """

    def __init__(self, *args, **kwds):
        self._limit = kwds.pop('limit', None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_limit()

    def _check_limit(self):
        if self._limit is not None:
            while len(self) > self._limit:
                self.popitem(last=False)


FEATURES = TerrainCache(limit=(max(MAX_HILL_RAD, MAX_BIOME_RAD) * 4) + world_gen['chunk_size'])


def gen_biome_chunk_features(chunk_pos, chunk_features_in_range, seed):
    chunk_biomes = []
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        if random.random() <= 0.05:

            slice_biome = {}
            slice_biome['x'] = x
            slice_biome['type'] = random.choice(biomes_population)
            slice_biome['radius'] = random.randint(world_gen['min_biome'], world_gen['max_biome'])

            # features[x]['biome'] = slice_biome

            chunk_biomes.append(slice_biome)

    return chunk_biomes


def gen_hill_chunk_features(chunk_pos, chunk_features_in_range, seed):
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


def gen_biome_slice_features(x, chunk_features_in_range, slice_features, seed):

    slice_biome = ('normal', None)
    slice_biome_distance_to_centre = float('inf')

    if chunk_features_in_range.get('biomes') is not None:
        for biome in chunk_features_in_range.get('biomes'):
            if (biome['x'] - biome['radius'] <= x and
                biome['x'] + biome['radius'] > x and
                abs(biome['x'] - x) < slice_biome_distance_to_centre):

                slice_biome_distance_to_centre = abs(biome['x'] - x)
                slice_biome = (biome['type'], biome['x'])

    return slice_biome


def gen_ground_height_slice_features(x, chunk_features_in_range, slice_features, seed):

    ground_height = world_gen['ground_height']

    hills_in_range = (hill for chunk_pos, fs in chunk_features_in_range.items() if fs.get('hills') for hill in fs['hills'])

    for hill in hills_in_range:
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


def gen_tree_features(x, chunk_features_in_range, slice_features, seed):

    biome = slice_features.get('slice_biome')
    ground_height = slice_features.get('ground_height')

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

        # Gausian tree height distrubution
        min_, max_ = 2, air_height - (len(center_leaves) - tree_feature['trunk_depth'])
        mean_height = (min_ + tree_data['mean_height'])
        max_std_dev = tree_data['max_std_dev']
        tree_feature['height'] = int(min(max(min_, random.gauss(mean_height, max_std_dev)), max_))

        return tree_feature


def gen_ore_features(x, chunk_features_in_range, slice_features, seed):

    ground_height = slice_features.get('ground_height')

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


def gen_grass_features(x, chunk_features_in_range, slice_features, seed):

    biome = slice_features.get('slice_biome')
    ground_height = slice_features.get('ground_height')

    biome_data = world_gen['biomes'][biome[0]]
    grass_chance = biome_data['grass']

    if random.random() <= grass_chance:

        grass_feature = {}
        grass_feature['y'] = ground_height

        return grass_feature


def gen_cave_features(features, chunk_pos, meta):

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
            for y in range(cave_y_res * (features[x]['ground_height'] - 2)):
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
        for _ in range(ca_iterations):
            new_air_points = set()

            for x in range(air_points_x_min, air_points_x_max):
                for y in range(cave_y_res * (features[x]['ground_height'] - 2)):
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


def generate_slice_features(features, chunk_pos, meta, feature_generator, feature_name, feature_buffer):

    log('generate_slice_features range', chunk_pos - feature_buffer[0], chunk_pos + world_gen['chunk_size'] + feature_buffer[1], m=1)

    # Generate dictionary of chunk-features (features on chunk positions) within the feature_buffer range.
    feature_buffer_chunk = (ceil(feature_buffer[0] / world_gen['chunk_size']) * world_gen['chunk_size'],
                            ceil(feature_buffer[1] / world_gen['chunk_size']) * world_gen['chunk_size'])
    feature_buffer_range = range(chunk_pos - feature_buffer_chunk[0],
                                 chunk_pos + world_gen['chunk_size'] + feature_buffer_chunk[1])
    chunk_features_in_range = {chunk: features[chunk] for chunk in feature_buffer_range if features.get(chunk)}

    for x in range(chunk_pos - feature_buffer[0], chunk_pos + world_gen['chunk_size'] + feature_buffer[1]):

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get(feature_name) is None:

            seed = str(meta['seed']) + str(x) + feature_name
            random.seed(seed)

            feature = feature_generator(x, chunk_features_in_range, features[x], seed)
            if feature is not None:
                features[x][feature_name] = feature


def generate_chunk_features(features, chunk_n, meta, feature_generator, feature_name, feature_buffer):
    for chunk_n_gen in range(chunk_n - feature_buffer[0], chunk_n + feature_buffer[1] + 1):
        chunk_pos = chunk_n_gen * world_gen['chunk_size']

        if features.get(chunk_pos) is None:
            # Init to empty, so 'no features' is cached.
            features[chunk_pos] = {}

        # If it is not None, it has all ready been generated.
        if features[chunk_pos].get(feature_name) is None:

            seed = str(meta['seed']) + str(chunk_pos) + feature_name
            random.seed(seed)

            feature = feature_generator(chunk_pos, features[chunk_pos], seed)
            if feature is not None:
                features[chunk_pos][feature_name] = feature


def gen_chunk_features(chunk_n, meta):
    log('', m=1)

    chunk_pos = chunk_n * world_gen['chunk_size']
    log('chunk', chunk_pos, m=1)

    generate_chunk_features(FEATURES, chunk_n, meta, gen_hill_chunk_features, 'hills', (MAX_HILL_CHUNKS, MAX_HILL_CHUNKS))
    generate_slice_features(FEATURES, chunk_pos, meta, gen_ground_height_slice_features, 'ground_height', (MAX_HILL_RAD, MAX_HILL_RAD))

    log('missing ground heights', set(range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD)) - set(pos for pos, fs in FEATURES.items() if fs.get('ground_height')), m=1, trunc=False)

    generate_chunk_features(FEATURES, chunk_n, meta, gen_biome_chunk_features, 'biomes', (MAX_BIOME_CHUNKS, MAX_BIOME_CHUNKS))
    generate_slice_features(FEATURES, chunk_pos, meta, gen_biome_slice_features, 'slice_biome', (MAX_BIOME_RAD, MAX_BIOME_RAD))

    gen_cave_features(FEATURES, chunk_pos, meta)

    generate_slice_features(FEATURES, chunk_pos, meta, gen_tree_features, 'tree', (MAX_HALF_TREE, MAX_HALF_TREE))
    generate_slice_features(FEATURES, chunk_pos, meta, gen_grass_features, 'grass', (0, 0))
    generate_slice_features(FEATURES, chunk_pos, meta, gen_ore_features, 'ores', MAX_ORE_RANGE)

    return FEATURES
