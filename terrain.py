from data import world_gen, blocks


EMPTY_SLICE = [' ' for y in range(world_gen['height'])]


def get_chunk_list(slice_list):
    return list(set(int(i) // world_gen['chunk_size'] for i in slice_list))


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


def spawn_hierarchy(tests):
    # TODO: Use argument expansion for tests
    return max(tests, key=lambda block: blocks[block]['hierarchy'])


def is_solid(block):
    return blocks[block]['solid']


def in_chunk(pos, chunk_pos):
    return chunk_pos <= pos < chunk_pos + world_gen['chunk_size']
