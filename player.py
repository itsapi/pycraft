import terrain


cursor_x = lambda cursor: {0:  0, 1:  1, 2: 1, 3: 0, 4: -1, 5: -1}[cursor]
cursor_y = lambda cursor: {0: -2, 1: -1, 2: 0, 3: 1, 4:  0, 5: -1}[cursor]


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
    for test_char, dir_, func in (('a', -1, left_slice), ('d', 1, right_slice)):
        if (char in test_char
            and not is_solid( func[head_y] )):

            if is_solid( func[feet_y] ):
                if (not is_solid( func[above_y] )
                    and not is_solid( player_slice[above_y] )):
                    dy = -1
                    dx = dir_
            else:
                dx = dir_

    # Jumps if up pressed, block below, no block above
    if (char in 'w' and y > 1
        and blocks[ player_slice[below_y] ][1]
        and not blocks[ player_slice[above_y] ][1]):

        dy = -1
        jump = 5

    return dx, dy, jump


def break_block(inp, map_, x, y, cursor, blocks):
    block_x = str(x + cursor_x(cursor))
    block_y = y + cursor_y(cursor)

    new_slices = {}

    # If pressing x and block is breakable
    if inp in 'k' and blocks[ map_[block_x][block_y] ][2]:
        new_slices[block_x] = map_[block_x]
        new_slices[block_x][block_y] = ' '
        redraw = True

    return new_slices


def respawn(meta):
    return meta['center'], 1


def move_cursor(inp):
    try:
        return {'j': -1, 'l': 1}[inp]
    except KeyError:
        return 0


def render_player(x, y, cursor):

    head = {
        'x': x,
        'y': y - 1,
        'char': '*'
    }

    feet = {
        'x': x,
        'y': y,
        'char': '^'
    }

    cursor = {
        'x': x + cursor_x(cursor),
        'y': y + cursor_y(cursor),
        'char': 'X'
    }

    return head, feet, cursor