import random
from math import ceil

from data import world_gen


# Maximum width of half a tree
max_half_tree = int(len(max(world_gen['trees'], key=lambda tree: len(tree))) / 2)


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

            if x < pos:
                gradient = gradient_r
            else:
                gradient = gradient_l

            # Check if still in range with new gradient
            if abs(pos-x) / gradient < world_gen['max_hill']:

                # Set height to height of hill minus distance from hill
                hill_height = (world_gen['ground_height'] +
                    random.randint(0, world_gen['max_hill']) - abs(pos-x)/gradient)
                # Make top of hill flat
                hill_height -= 1 if pos == x else 0

                slice_height_ = max(slice_height_, hill_height)

    return int(slice_height_)


def add_tree(slice_, pos, meta, blocks):
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
                            slice_[sy] = spawn_hierarchy(blocks, ('@', slice_[sy]))

            if x == pos:
                # Add trunk to slice
                for i in range(air_height - tree_height,
                               air_height):
                    slice_[i] = spawn_hierarchy(blocks, ('|', slice_[i]))

    return slice_


def biome(pos, meta):
    biome_type = []

    # Check surrounding slices for a biome marker
    for boime_x in range(pos - int(world_gen['max_biome_size'] / 2),
                         pos + int(world_gen['max_biome_size'] / 2)):
        # Set seed for random numbers based on position
        random.seed(str(meta['seed']) + str(boime_x) + 'biome')

        # Generate a biome marker with a 5% chance
        if random.random() <= 0.05:
            biome_type.append(random.choice(world_gen['biome_tree_weights']))

    # If not plains or forest, it's normal
    return max(set(biome_type), key=biome_type.count) if biome_type else .05


def add_ores(slice_, pos, meta, blocks, slice_height_):
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
                    slice_[sy] = spawn_hierarchy(blocks, (ore['char'], slice_[sy]))

    return slice_


def add_tall_grass(slice_, pos, meta, blocks, slice_height_):
    # Set seed for random numbers based on position and grass
    random.seed(str(meta['seed']) + str(pos) + 'grass')

    # Gernerate a grass with a probability
    if random.random() <= world_gen['tall_grass_rate']:
        sy = world_gen['height'] - slice_height_ - 1
        slice_[sy] = spawn_hierarchy(blocks, ('v', slice_[sy]))

    return slice_


def gen_slice(pos, meta, blocks):
    slice_height_ = slice_height(pos, meta)

    # Form slice of sky, grass, stone, bedrock
    slice_ = (
        [' '] * (world_gen['height'] - slice_height_) +
        ['-'] +
        ['#'] * (slice_height_ - 2) + # 2 for grass and bedrock
        ['_']
    )

    slice_ = add_tree(slice_, pos, meta, blocks)
    slice_ = add_ores(slice_, pos, meta, blocks, slice_height_)
    slice_ = add_tall_grass(slice_, pos, meta, blocks, slice_height_)

    return slice_


def detect_edges(map_, edges):
    slices = []
    for pos in range(*edges):
        if not str(pos) in map_:
            slices.append(pos)

    return slices


def spawn_hierarchy(blocks, tests):
    return max(tests, key=lambda block: blocks[block]['hierarchy'])


def is_solid(blocks, block):
    return blocks[block]['solid']


def ground_height(slice_, blocks):
    return next(i for i, block in enumerate(slice_) if blocks[block]['solid'])
