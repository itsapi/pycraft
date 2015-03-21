import terrain
from console import supported_chars, CLS
from colors import *


cursor_x = {0:  0, 1:  1, 2: 1, 3: 0, 4: -1, 5: -1}
cursor_y = {0: -2, 1: -1, 2: 0, 3: 1, 4:  0, 5: -1}


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
        if map_[block_x][block_y] == ' ' and len(inv):
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
        'x': x + cursor_x[cursor],
        'y': y + cursor_y[cursor],
        'char': 'X'
    }

    return (head, feet) if c_hidden else (head, feet, cursor)


def render_grid(grid, blocks, sel=None):
    h, v, tl, t, tr, l, m, r, bl, b, br = \
        supported_chars('─│╭┬╮├┼┤╰┴╯', '─│┌┬┐├┼┤└┴┘', '-|+++++++++')

    # Find maximum length of the num column.
    max_n_w = len(str(max(map(lambda s: s['num'], grid)))) if len(grid) else 1

    out = []
    out.append(tl + (h*3) + t + (h*(max_n_w+2)) + tr)
    for i, slot in enumerate(grid):
        if slot is not None:
            block_char = blocks[slot['block']]['char']
            num = slot['num']
        else:
            block_char, num = ' ', ''

        # Have to do the padding before color because the color
        #   messes with the char count. (The block will always be 1 char wide.)
        num = '{:{max}}'.format(num, max=max_n_w)

        out.append('{v} {b} {v} {n} {v}'.format(
            b=colorStr(block_char, bg=None),
            n=colorStr(num, bg=RED) if i == sel else num,
            v=v
        ))

        if not i == len(grid) - 1:
            out.append(l + (h*3) + m + (h*(max_n_w+2)) + r)

    out.append(bl + (h*3) + b + (h*(max_n_w+2)) + br)
    return out


def get_crafting(inv, crafting_sel, blocks):
    inv = dict(map(lambda a: (a['block'], a['num']), inv))
    crafting = []

    for block in blocks.values():
        if 'recipe' in block:
            can_craft = True
            for c, n in block['recipe'].items():
                if not (c in inv and n <= inv[c]):
                    can_craft = False
            if can_craft:
                crafting.append({'block': block['char'], 'num': 1})

    return crafting, max(crafting_sel, len(crafting) - 1)


def crafting(inp, inv, inv_sel, crafting_list, crafting_sel, blocks):
    dinv = False

    if inp in 'i' and len(crafting_list):
        dinv = True
        block = crafting_list[crafting_sel]

        recipe = blocks[block['block']]['recipe']
        for c, n in recipe.items():
            for i, b in enumerate(inv):
                if b['block'] == c:
                    rem_inv(inv, i, n)
                    inv_sel -= inv_sel > i or len(inv) == inv_sel

        add_inv(inv, block['block'], block['num'])

    return inv, inv_sel, crafting_list, dinv


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
