import terrain


def get_pos_delta(char, map_, x, y, blocks, jump):

    left_slice = map_[str(x - 1)]
    player_slice = map_[str(x)]
    right_slice = map_[str(x + 1)]

    feet_y = y
    head_y = y - 1
    below_y = y + 1
    above_y = y - 2

    dy = 0
    dx = 0

    is_solid = lambda block: terrain.is_solid(blocks, block)

    # Calculate change in x pos for left and right movement
    for test_char, dir_, func in (('aA', -1, left_slice), ('dD', 1, right_slice)):
        if (char in test_char
            and not is_solid( func[head_y] )):

            if is_solid( func[feet_y] ):
                if not is_solid( func[above_y] ):
                    dy = -1
                    dx = dir_
            else:
                dx = dir_

    # Jumps if up pressed, block below, no block above
    if (char in 'wW' and y > 1
        and blocks[ player_slice[below_y] ][1]
        and not blocks[ player_slice[above_y] ][1]):

        dy = -1
        jump = 5

    return dx, dy, jump


def break_block(inp, map_, x, y, blocks):
    block_x = str(x)
    block_y = y + 1

    new_slices = {}

    # If pressing x and block is breakable
    if inp in 'fF' and blocks[ map_[block_x][block_y] ][2]:
        new_slices[block_x] = map_[block_x]
        new_slices[block_x][block_y] = ' '
        redraw = True

    return new_slices


def respawn(meta):
    return meta['center'], 1