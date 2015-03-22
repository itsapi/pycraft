import terrain
from console import supported_chars, CLS
from colors import *


cursor_x = {0:  0, 1:  1, 2: 1, 3: 0, 4: -1, 5: -1}
cursor_y = {0: -2, 1: -1, 2: 0, 3: 1, 4:  0, 5: -1}

INV_TITLE = 'Inventory'
CRAFT_TITLE = 'Crafting'


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
        and not is_solid( player_slice[above_y] )
            and (
                is_solid( player_slice[below_y] )
                or player_slice[feet_y] == '=' )):

        dy = -1
        jump = 5

    return dx, dy, jump


def cursor_func(inp, map_, x, y, cursor, inv_sel, meta, blocks):
    block_x = str(x + cursor_x[cursor])
    block_y = y + cursor_y[cursor]
    dinv = False
    inv = meta['inv']

    slices = {}

    if inp in 'k' and block_y >= 0:

        # If pressing k and block is air
        if (map_[block_x][block_y] == ' ' and len(inv) and
            blocks[ inv[inv_sel]['block'] ]['breakable']):

            # Place block in world from selected inv slot
            slices[block_x] = map_[block_x]
            slices[block_x][block_y] = inv[inv_sel]['block']
            inv, inv_sel = rem_inv(inv, inv_sel)
            dinv = True

        # If pressing k and block is not air and breakable
        elif blocks[ map_[block_x][block_y] ]['breakable']:

            # Destroy block
            block = map_[block_x][block_y]
            slices[block_x] = map_[block_x]
            slices[block_x][block_y] = ' '
            inv = add_inv(inv, block)
            dinv = True

    return slices, inv, inv_sel, dinv


def respawn(meta):
    return meta['spawn'], 1


def move_cursor(inp):
    return {'j': -1, 'l': 1}.get(inp, 0)


def move_sel(inp):
    return {'u': -1, 'o': 1}.get(inp, 0)


def cursor_colour(x, y, cursor, map_, blocks):
    block = blocks[ map_[ str(x + cursor_x[cursor]) ][ y + cursor_y[cursor] ] ]
    return [RED, WHITE][block['breakable']]


def render_player(x, y, cursor, colour, c_hidden):

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
        'x': x + cursor_x[cursor],
        'y': y + cursor_y[cursor],
        'char': 'X',
        'colour': colour
    }

    return (head, feet) if c_hidden else (head, feet, cursor)


def render_grid(title, selected, grid, blocks, sel=None):
    h, v, tl, t, tr, l, m, r, bl, b, br = \
        supported_chars('─│╭┬╮├┼┤╰┴╯', '─│┌┬┐├┼┤└┴┘', '-|+++++++++')

    # Find maximum length of the num column.
    max_n_w = len(str(max(map(lambda s: s['num'], grid)))) if len(grid) else 1

    # Figure out number of trailing spaces to make the grid same width as the title.
    #     |   block    |         num          |
    top = tl + (h*3) + t + (h*(max_n_w+2)) + tr
    trailing = ' ' * max(0, len(title) - len(top))

    out = [
        (colorStr(title, style=BOLD) if selected else title) +
            ' ' * max(0, len(top) - len(title)),
        top + trailing
    ]

    for i, slot in enumerate(grid):
        if slot is not None:
            block_char = blocks[slot['block']]['char']
            num = slot['num']
        else:
            block_char, num = ' ', ''

        # Have to do the padding before colour because the colour
        #   messes with the char count. (The block will always be 1 char wide.)
        num = '{:{max}}'.format(num, max=max_n_w)

        out.append('{v} {b} {v} {n} {v}{trail}'.format(
            b=colorStr(block_char, bg=None),
            n=colorStr(num, bg=RED) if i == sel else num,
            v=v,
            trail=trailing
        ))

        if not i == len(grid) - 1:
            out.append(l + (h*3) + m + (h*(max_n_w+2)) + r + trailing)

    out.append(bl + (h*3) + b + (h*(max_n_w+2)) + br + trailing)
    return out


def title(t, selected):
    return colorStr(t, style=BOLD) if selected else t


def get_crafting(inv, crafting_sel, blocks):
    """ Makes a list of blocks you can craft """

    inv = dict(map(lambda a: (a['block'], a['num']), inv))
    crafting = []

    for char, block in blocks.items():
        if 'recipe' in block:
            can_craft = True
            for ingredient, n in block['recipe'].items():
                if not (ingredient in inv and n <= inv[ingredient]):
                    can_craft = False
            if can_craft:
                crafting.append({'block': char,
                                 'num': block.get('crafts', 1)})

    return crafting, max(crafting_sel, len(crafting) - 1)


def craft_num(inp, inv, crafting_list, crafting_sel, blocks):
    dcraft = False

    if inp in '-=':
        dn = '-='.find(inp)*2 - 1

        inv = dict(map(lambda a: (a['block'], a['num']), inv))

        craft = crafting_list[crafting_sel]
        block = blocks[craft['block']]

        n_crafts = max(1, dn + int(craft['num'] / block.get('crafts', 1)))

        can_craft = True
        for ingredient, n in block['recipe'].items():
            if not (ingredient in inv and (n * n_crafts) <= inv[ingredient]):
                can_craft = False

        if can_craft:
            crafting_list[crafting_sel]['num'] = n_crafts * block.get('crafts', 1)
            dcraft = True

    return crafting_list, dcraft


def crafting(inp, inv, inv_sel, crafting_list, crafting_sel, blocks):
    """ Crafts the selected item in crafting_list """

    dcraft = False

    if inp in 'i' and len(crafting_list):
        dcraft = True
        craft = crafting_list[crafting_sel]

        block = blocks[craft['block']]
        for ingredient, n in block['recipe'].items():
            for i, b in enumerate(inv):
                if b['block'] == ingredient:
                    inv, _ = rem_inv(inv, i, n * int(craft['num'] / block.get('crafts', 1)))

                    # Decrements inv_sel if you're at the end of the list
                    #   or an item is removed below you in the list.
                    inv_sel -= inv_sel > i or len(inv) == inv_sel

        add_inv(inv, craft['block'], craft['num'])

    return inv, inv_sel, crafting_list, dcraft


def inv_label(inv, inv_sel, blocks):
    try:
        return blocks[inv[inv_sel]['block']]['name']
    except IndexError:
        return ''


def add_inv(inv, block, n=1):
    placed = False

    for i, slot in enumerate(inv):
        if slot['block'] == block:
            inv[i]['num'] += n
            placed = True
            break

    if placed is False:
        inv.append({'block': block, 'num': n})

    return inv


def rem_inv(inv, inv_sel, n=1):
    if inv[inv_sel]['num'] == n:
        inv.remove(inv[inv_sel])

        if inv_sel == len(inv):
            inv_sel -= 1
    else:
        inv[inv_sel]['num'] -= n

    return inv, inv_sel
