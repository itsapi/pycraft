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

    new_slices = {}

    if inp in 'k' and block_y >= 0:
        # If pressing k and block is air
        if map_[block_x][block_y] == ' ':
            try:
                new_slices[block_x] = map_[block_x]
                new_slices[block_x][block_y] = inv[str(inv_sel)][0]
                inv = rem_inv(inv, inv_sel)
                redraw = True
            except (KeyError, TypeError):
                pass
        # If pressing k and block is not air and breakable
        elif blocks[ map_[block_x][block_y] ]['breakable']:
            block = map_[block_x][block_y]
            new_slices[block_x] = map_[block_x]
            new_slices[block_x][block_y] = ' '
            inv = add_inv(inv, block)
            redraw = True

    return new_slices, inv


def respawn(meta):
    return meta['spawn'], 1


def move_cursor(inp):
    try:
        return {'j': -1, 'l': 1}[inp]
    except KeyError:
        return 0


def move_inv_sel(inp):
    try:
        return {'n': -1, 'm': 1}[inp]
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
    for slot in range(INV_SLOTS):
        try:
            block = blocks[inv[str(slot)][0]]['char']
            num = inv[str(slot)][1]
        except (KeyError, TypeError):
            block, num = '', ''
        out.append('| {:1} | {:2} |{}'.format(block, num, ' *' if slot == inv_sel else ''))
        out.append('-' * 10)
    return out


def add_inv(inv, item):
    found = False
    for num, slot in inv.items():
        try:
            if slot[0] == item and slot[1] < MAX_ITEM:
                inv[str(num)][1] += 1
                found = True
                break
        except TypeError:
            pass

    if not found:
        for num in range(INV_SLOTS):
            try:
                slot = inv[str(num)]
            except (KeyError, TypeError):
                inv[str(num)] = [item, 1]
                break
    return inv


def rem_inv(inv, inv_sel):
    inv_slot = inv[str(inv_sel)]
    if inv_slot[1] == 1:
        inv_slot = None
    else:
        inv_slot[1] -= 1
    inv[str(inv_sel)] = inv_slot
    return inv
