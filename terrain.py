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
    connected_to_ground = explore_map(map_, edges, start_pos, [])

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


def explore_map(map_, edges, start_pos, found):
    if (start_pos[1] >= 0 and start_pos[1] < world_gen['height'] and
            start_pos not in found and
            start_pos[0] in range(edges[0]-1, edges[1]+1)):

        try:
            current_block = map_[start_pos[0]][start_pos[1]]
        except (IndexError, KeyError):
            current_block = None

        if (current_block is not None and
                is_solid(current_block)) or start_pos[0] in (edges[0]-1, edges[1]):

            found.append(start_pos)
            for diff in ((x, y) for x in range(3) for y in range(3)):
                pos = (start_pos[0] + diff[0] - 1, start_pos[1] + diff[1] - 1)
                found = explore_map(map_, edges, pos, found)

    return found


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


# TODO: This probably shouldn't stay here...
features = None
def init_features():
    global features
    cache_size = (world_gen['max_biome'] * 4) + world_gen['chunk_size']
    features = TerrainCache(limit=cache_size)

init_features()


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


def gen_biome_features(features, chunk_pos, meta):
    for x in range(chunk_pos - world_gen['max_biome'], chunk_pos + world_gen['chunk_size'] + world_gen['max_biome']):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('biome') is None:

            random.seed(str(meta['seed']) + str(x) + 'biome')
            if random.random() <= 0.05:

                # TODO: Move outside function
                biomes_population = []
                for name, data in world_gen['biomes'].items():
                    biomes_population.extend([name] * int(data['chance'] * 100))

                attrs = {}
                attrs['type'] = random.choice(sorted(biomes_population))
                attrs['radius'] = random.randint(world_gen['min_biome'], world_gen['max_biome'])

                features[x]['biome'] = attrs


def gen_hill_features(features, chunk_pos, meta):
    for x in range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('hill') is None:

            random.seed(str(meta['seed']) + str(x) + 'hill')
            if random.random() <= 0.05:

                attrs = {}
                attrs['gradient_l'] = random.randint(1, world_gen['min_grad'])
                attrs['gradient_r'] = random.randint(1, world_gen['min_grad'])
                attrs['height'] = random.randint(0, world_gen['max_hill'])

                features[x]['hill'] = attrs


def gen_tree_features(features, ground_heights, slices_biome, chunk_pos, meta):
    for x in range(chunk_pos - MAX_HALF_TREE, chunk_pos + world_gen['chunk_size'] + MAX_HALF_TREE):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('tree') is None:

            biome_data = world_gen['biomes'][slices_biome[x][0]]
            boime_tree_chance = biome_data['trees']

            random.seed(str(meta['seed']) + str(x) + 'tree')
            type_ = random.randint(0, len(world_gen['trees'])-1)
            tree_data = world_gen['trees'][type_]

            tree_chance = boime_tree_chance * tree_data['chance']

            if random.random() <= tree_chance:

                attrs = {}
                attrs['type'] = type_

                leaves = tree_data['leaves']

                # Centre tree slice (contains trunk)
                # TODO: This calculation could be done on start-up, and stored
                #         with each tree type.
                center_leaves = leaves[int(len(leaves) / 2)]
                if 1 in center_leaves:
                    attrs['trunk_depth'] = center_leaves[::-1].index(1)
                else:
                    attrs['trunk_depth'] = len(center_leaves)


                # Get space above ground
                air_height = world_gen['height'] - ground_heights[x]
                tree_height = air_height - (len(center_leaves) - attrs['trunk_depth'])
                attrs['height'] = random.randint(2, max(tree_height, 2))

                features[x]['tree'] = attrs


def gen_ore_features(features, ground_heights, slices_biome, chunk_pos, meta):
    for x in range(chunk_pos - MAX_ORE_RANGE[0], chunk_pos + world_gen['chunk_size'] + MAX_ORE_RANGE[1]):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # Ores
        # NOTE: Ores seem to be the way to model the generalisation of the
        #         rest of the features after
        for name, ore in world_gen['ores'].items():
            feature_name = name + '_ore_root'

            # If it is not None, it has all ready been generated.
            if features[x].get(feature_name) is None:

                random.seed(str(meta['seed']) + str(x) + feature_name)
                if random.random() <= ore['chance']:

                    upper = int(world_gen['height'] * ore['upper'])
                    lower = int(world_gen['height'] * ore['lower'])

                    attrs = {}
                    attrs['root_height'] = world_gen['height'] - random.randint(
                        lower, min(upper, (ground_heights[x] - 1))  # -1 for grass.
                    )

                    # Generates ore at random position around root ore
                    pot_vain_blocks = ore['vain_size'] ** 2

                    # Describes the shape of the vain,
                    #   top to bottom, left to right.
                    attrs['vain_shape'] = [b / 100 for b in random.sample(range(0, 100), pot_vain_blocks)]

                    features[x][feature_name] = attrs


def gen_grass_features(features, ground_heights, slices_biome, chunk_pos, meta):
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('grass') is None:

            biome_data = world_gen['biomes'][slices_biome[x][0]]
            grass_chance = biome_data['grass']

            random.seed(str(meta['seed']) + str(x) + 'grass')
            if random.random() <= grass_chance:

                attrs = {}
                attrs['y'] = ground_heights[x]

                features[x]['grass'] = attrs


def gen_cave_features(features, ground_heights, slices_biome, chunk_pos, meta):

    def gen_segments(x, y, old_w, old_d):
        new_segments = []
        d = old_d % 360

        target = (90, 270)[d > 180]
        upper = target - d
        lower = random.randint(-10, 10)
        if lower > upper:
            lower, upper = upper, lower
        d += random.randint(lower, upper)

        dx = int(10*sin(radians(d)))
        dy = int(10*cos(radians(d)))
        width = min(3, max(1, old_w + random.randint(-1, 1)))
        log(d, dx, dy, m='cave')

        if (x+dx in range(chunk_pos - world_gen['max_cave_radius'],
                          chunk_pos + world_gen['max_cave_radius'] + world_gen['chunk_size']) and
           0 < y+dy < ground_heights[x+dx]):

            new_segments.append(((x, y), (dx, dy), width))
            new_segments += gen_segments(x + dx, y + dy, width, d)
            if random.random() < 0.1:
                new_segments += gen_segments(x + dx, y + dy, width, random.choice([-90, 90]) + d)

        return new_segments

    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):

        # TODO: Each of these `if` blocks should be abstracted into a function
        #         which just returns the `attrs` object.

        if features.get(x) is None:
            # Init to empty, so 'no features' is cached.
            features[x] = {}

        # If it is not None, it has all ready been generated.
        if features[x].get('cave') is None:

            random.seed(str(meta['seed']) + str(x) + 'cave')
            if random.random() <= world_gen['cave_chance']:

                attrs = {}
                attrs['y'] = ground_heights[x] + 1

                attrs['segments'] = gen_segments(x, attrs['y'], 2, 180)

                features[x]['cave'] = attrs
                log('got a cave', features[x]['cave'], m='cave')


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

            if in_chunk(block_x, chunk_pos):
                # Won't allow ore above surface
                if world_gen['height'] > block_y > world_gen['height'] - ground_heights[block_x]:
                    chunk[block_x][block_y] = spawn_hierarchy((ore['char'], chunk[block_x][block_y]))


def build_cave(chunk, chunk_pos, x, cave_feature, ground_heights):
    """ Adds caves at x to the chunk. """

    for segment in cave_feature['segments']:
        (sx, sy), (dx, dy), r = segment

        x_quad = abs(dx) >= abs(dy)
        r -= (r/2) * abs(cos(atan2(dy, dx)))
        log(r, x_quad, m='cave')

        if x_quad:
            if dx < 0:
                sx = sx + dx
                dx *= -1
                sy = sy + dy
                dy *= -1

            ry = int(r * cos(atan2(dy, dx)))
            for u in range(sx, sx + dx):
                if in_chunk(u, chunk_pos):
                    y_intercept = int(world_gen['height'] - (sy + dy * (u - sx) / dx))

                    for zy in range(y_intercept-ry, y_intercept+ry+1):
                        chunk[u][zy] = ' '

        else:
            if dy < 0:
                sy = sy + dy
                dy *= -1
                sx = sx + dx
                dx *= -1

            rx = int(r * cos(atan2(dx, dy)))
            for v in range(sy, sy + dy):
                x_intercept = int((sx + dx * (v - sy) / dy))

                for zx in range(x_intercept-rx, x_intercept+rx):
                    if in_chunk(zx, chunk_pos):
                        chunk[zx][world_gen['height'] - v] = ' '


def gen_chunk(chunk_n, meta):
    chunk_pos = chunk_n * world_gen['chunk_size']

    # TODO: Allow more than one feature per x in features?

    # First generate all the features we will need
    #   for all the slice is in this chunk

    gen_biome_features(features, chunk_pos, meta)
    gen_hill_features(features, chunk_pos, meta)

    # Generate hill heights and biomes map for the tree and ore generation.
    ground_heights = {x: world_gen['ground_height'] for x in range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD)}
    # Store feature_x with the value for calculating precedence.
    slices_biome = {x: ('normal', None) for x in range(chunk_pos - world_gen['max_biome'], chunk_pos + world_gen['chunk_size'] + world_gen['max_biome'])}

    for feature_x, slice_features in features.items():
        feature_x = int(feature_x)

        for feature_name, feature in slice_features.items():

            if feature_name == 'hill':

                for d_x in range(-feature['height'] * feature['gradient_l'],
                                 feature['height'] * feature['gradient_r']):
                    x = feature_x + d_x

                    gradient = feature['gradient_l'] if d_x < 0 else feature['gradient_r']
                    hill_height = int(feature['height'] - (abs(d_x) / gradient))

                    if d_x == 0:
                        hill_height -= 1

                    ground_height = world_gen['ground_height'] + hill_height

                    old_height = ground_heights.get(x, 0)
                    ground_heights[x] = max(ground_height, old_height)

            elif feature_name == 'biome':

                for d_x in range(-feature['radius'], feature['radius']):
                    x = feature_x + d_x

                    if x in slices_biome:
                        previous_slice_biome_feature_x = slices_biome[x][1]

                        if (previous_slice_biome_feature_x is None or
                                previous_slice_biome_feature_x < feature_x):
                            slices_biome[x] = (feature['type'], feature_x)

    chunk = {}
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):
        chunk[x] = (
            [' '] * (world_gen['height'] - ground_heights[x]) +
            ['-'] +
            ['#'] * (ground_heights[x] - 2) +  # 2 for grass and bedrock
            ['_']
        )

    int_x = list(map(int, ground_heights.keys()))
    log('chunk', chunk_pos, m=1)
    log('max', max(int_x), m=1)
    log('min', min(int_x), m=1)
    log('gh diff', set(range(chunk_pos - MAX_HILL_RAD, chunk_pos + world_gen['chunk_size'] + MAX_HILL_RAD)) - set(int_x), m=1, trunc=False)
    log('slices_biome', list(filter(lambda slice_: (int(slice_[0])%16 == 0) or (int(slice_[0])+1)%16 == 0, sorted(slices_biome.items()))), m=1, trunc=False)

    gen_cave_features(features, ground_heights, slices_biome, chunk_pos, meta)
    gen_tree_features(features, ground_heights, slices_biome, chunk_pos, meta)
    gen_ore_features(features, ground_heights, slices_biome, chunk_pos, meta)
    gen_grass_features(features, ground_heights, slices_biome, chunk_pos, meta)

    log('chunk_pos', chunk_pos, m=1)
    tree_features = list(filter(lambda f: f[1].get('tree'), features.items()))
    log('trees in cache\n', [str(f[0]) for f in tree_features], m=1, trunc=0)
    log('trees in range', [str(f[0]) for f in tree_features if (chunk_pos <= int(f[0]) < chunk_pos + world_gen['chunk_size'])], m=1, trunc=0)

    # Insert trees and ores
    for feature_x, slice_features in features.items():
        feature_x = int(feature_x)

        for feature_name, feature in slice_features.items():

            if feature_name == 'tree':
                build_tree(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'grass':
                build_grass(chunk, chunk_pos, feature_x, feature, ground_heights)

            elif feature_name == 'cave':
                build_cave(chunk, chunk_pos, feature_x, feature, ground_heights)

            else:
                for name, ore in world_gen['ores'].items():
                    ore_name = name + '_ore_root'

                    if feature_name == ore_name:
                        build_ore(chunk, chunk_pos, feature_x, feature, ore, ground_heights)
                        break

    return chunk, {x: s for x, s in ground_heights.items() if x in range(chunk_pos, chunk_pos+world_gen['chunk_size'])}
