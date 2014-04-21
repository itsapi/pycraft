import terrain


cursor_x = lambda cursor: {0:  0, 1:  1, 2: 1, 3: 0, 4: -1, 5: -1}[cursor]
cursor_y = lambda cursor: {0: -2, 1: -1, 2: 0, 3: 1, 4:  0, 5: -1}[cursor]

INV_SLOTS = 10
MAX_ITEM = 64


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
        and blocks[ player_slice[below_y] ]['solid']
        and not blocks[ player_slice[above_y] ]['solid']):

        dy = -1
        jump = 5

    return dx, dy, jump


def cursor_func(inp, map_, x, y, cursor, inv_sel, inv, blocks):
    block_x = str(x + cursor_x(cursor))
    block_y = y + cursor_y(cursor)
    dinv = False

    new_slices = {}

    if inp in 'k' and block_y >= 0:
        # If pressing k and block is air
        if map_[block_x][block_y] == ' ' and inv[inv_sel] is not None:
            # Place block in world from selected inv slot
            new_slices[block_x] = map_[block_x]
            new_slices[block_x][block_y] = inv[inv_sel]['block']
            inv = rem_inv(inv, inv_sel)
            dinv = True
        # If pressing k and block is not air and breakable
        elif blocks[ map_[block_x][block_y] ]['breakable']:
            # Distroy block
            block = map_[block_x][block_y]
            new_slices[block_x] = map_[block_x]
            new_slices[block_x][block_y] = ' '
            inv = add_inv(inv, block)
            dinv = True

    # If pressing b remove 1 item from inv slot
    if inp in 'b':
        inv = rem_inv(inv, inv_sel)
        dinv = True
    # If pressing ctrl-b remove stack from inv slot
    if ord(inp) == 2:
        inv = rem_inv(inv, inv_sel, MAX_ITEM)
        dinv = True

    return new_slices, inv, dinv


def respawn(meta):
    return meta['spawn'], 1


def move_cursor(inp):
    try:
        return {'j': -1, 'l': 1}[inp]
    except KeyError:
        return 0


def move_inv_sel(inp):
    try:
        return {'h': -1, ';': 1}[inp]
    except KeyError:
        return 0


def render_player(x, y, cursor, c_hidden):

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

    return (head, feet) if c_hidden else (head, feet, cursor)


def render_inv(inv_sel, inv, blocks):
    out = []
    out.append('-' * 10)
    for i, slot in enumerate(inv):
        if slot is not None:
            block = blocks[slot['block']]['char']
            num = slot['num']
        else:
            block, num = '', ''
        out.append('| {:1} | {:2} |{}'.format(block, num, ' *' if i == inv_sel else ''))
        out.append('-' * 10)
    return out


def add_inv(inv, block):
    empty = False
    placed = False
    for i, slot in enumerate(inv):
        if slot is not None and slot['block'] == block and slot['num'] < MAX_ITEM:
            inv[i]['num'] += 1
            placed = True
        elif slot is None and empty is False:
            empty = i

    if placed is False and empty is not False:
        inv[empty] = {'block': block, 'num': 1}

    return inv


def rem_inv(inv, inv_sel, num=1):
    if inv[inv_sel]['num'] > num:
        inv[inv_sel]['num'] -= num
    else:
        inv[inv_sel] = None
    return inv
