from data import world_gen
from terrain import in_chunk, spawn_hierarchy
from console import log, DEBUG

import terrain_gen, terrain


def ground_height_feature(features, x):
    ground_height = world_gen['ground_height']

    slice_features = features.get(x)
    if slice_features and slice_features.get('ground_height'):
        ground_height = slice_features['ground_height']

    return ground_height


def build_tree(chunk, chunk_pos, x, tree_feature, features):
    """ Adds a tree feature at x to the chunk. """

    # Add trunk
    if in_chunk(x, chunk_pos):
        air_height = world_gen['height'] - ground_height_feature(features, x)
        for trunk_y in range(air_height - tree_feature['height'], air_height - (bool(DEBUG) * 3)):
            chunk[x][trunk_y] = spawn_hierarchy(('|', chunk[x][trunk_y]))

    # Add leaves
    leaves = world_gen['trees'][tree_feature['type']]['leaves']
    half_leaves = int(len(leaves) / 2)

    for leaf_dx, leaf_slice in enumerate(leaves):
        leaf_x = x + (leaf_dx - half_leaves)

        if in_chunk(leaf_x, chunk_pos):
            air_height = world_gen['height'] - ground_height_feature(features, x)
            leaf_height = air_height - tree_feature['height'] - len(leaf_slice) + tree_feature['trunk_depth']

            for leaf_dy, leaf in enumerate(leaf_slice):
                if (bool(DEBUG) and leaf_dy == 0) or (not bool(DEBUG) and leaf):
                    leaf_y = leaf_height + leaf_dy
                    chunk[leaf_x][leaf_y] = spawn_hierarchy(('@', chunk[leaf_x][leaf_y]))


def build_grass(chunk, chunk_pos, x, grass_feature, features):
    """ Adds a grass feature at x to the chunk. """

    if in_chunk(x, chunk_pos):
        grass_y = world_gen['height'] - ground_height_feature(features, x) - 1
        chunk[x][grass_y] = spawn_hierarchy(('v', chunk[x][grass_y]))


def build_ore(chunk, chunk_pos, x, ore_feature, ore, features):
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

            if not world_gen['height'] > block_y > world_gen['height'] - ground_height_feature(features, block_x):
                continue

            if chunk[block_x][block_y] is ' ':
                continue

            chunk[block_x][block_y] = spawn_hierarchy((ore['char'], chunk[block_x][block_y]))


def build_cave(chunk, chunk_pos, x, cave_feature, features):
    """ Adds caves at x to the chunk. """

    for (world_x, y) in cave_feature:
        if in_chunk(world_x, chunk_pos):
            chunk[world_x][int(y)] = ' '


def build_chunk(chunk_n, meta):
    chunk_pos = chunk_n * world_gen['chunk_size']

    chunk_features = terrain_gen.gen_chunk_features(chunk_n, meta)

    chunk_ground_heights = {}
    chunk = {}
    for x in range(chunk_pos, chunk_pos + world_gen['chunk_size']):
        slice_features = chunk_features.get(x)

        chunk_ground_heights[x] = ground_height_feature(chunk_features, x)

        chunk[x] = (
            [' '] * (world_gen['height'] - chunk_ground_heights[x]) +
            ['-'] +
            ['#'] * (chunk_ground_heights[x] - 2) +  # 2 for grass and bedrock
            ['_']
        )

    for x, slice_features in chunk_features.items():
        x = int(x)

        for feature_name, feature in slice_features.items():

            if feature_name == 'tree':
                build_tree(chunk, chunk_pos, x, feature, chunk_features)

            elif feature_name == 'grass':
                build_grass(chunk, chunk_pos, x, feature, chunk_features)

            elif feature_name == 'cave':
                build_cave(chunk, chunk_pos, x, feature, chunk_features)

            else:
                for name, ore in world_gen['ores'].items():
                    ore_name = name + '_ore_root'

                    if feature_name == ore_name:
                        build_ore(chunk, chunk_pos, x, feature, ore, chunk_features)
                        break

    return chunk, chunk_ground_heights
