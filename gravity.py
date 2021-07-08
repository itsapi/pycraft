from data import world_gen
from terrain import is_solid


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
