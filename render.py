from math import cos, sin

from colours import *
from console import *
from data import world_gen, blocks


sun_y = world_gen['height'] - world_gen['ground_height']
max_light = max(map(lambda b: b.get('light', 0), blocks.values()))


def render_map(map_, objects, blocks, sun, lights, tick, last_frame):
    """
        Prints out a frame of the game.

        Takes:
        - map_: a 2D list of blocks.
        - objects: a list of dictionaries:
            {'x': int, 'y': int, 'char': block}
        - blocks: the main dictionary describing the blocks in the game.
        - sun: (x, y) position of the sun.
        - lights: a list of light sources:
            {'x': int, 'y': int, 'radius': int}
        - tick: the game time.
    """

    # Sorts the dict as a list by pos
    map_ = list(map_.items())
    map_.sort(key=lambda item: int(item[0]))

    # map_ = [[0, '##  '],
    #         [1, '### '],
    #         [2, '##  ']]

    # Separates the pos and data
    map_ = tuple(zip(*map_))[1]

    # Orientates the data
    map_ = zip(*map_)

    diff = ''
    this_frame = []

    for y, row in enumerate(map_):
        this_frame.append([])

        for x, pixel in enumerate(row):

            pixel_out = calc_pixel(x, y, pixel, objects, blocks, sun, lights, tick)
            this_frame[-1].append(pixel_out)

            try:
                if not last_frame[y][x] == pixel_out:
                    # Changed
                    diff += POS_STR(x, y, pixel_out)
            except IndexError:
                # Doesn't exsit
                diff += POS_STR(x, y, pixel_out)

    return diff, this_frame


def obj_pixel(x, y, objects, blocks):

    for object_ in objects:
        if object_['x'] == x and object_['y'] == y:

            # Objects can override their block colour
            colour = object_.get('colour', blocks[object_['char']]['colours']['fg'])

            return object_['char'], colour

    return None, None


def calc_pixel(x, y, pixel_f, objects, blocks, sun, lights, tick):

    # Add any objects
    object_, obj_colour = obj_pixel(x, y, objects, blocks)

    # Add sky behind blocks without objects
    if object_:
        pixel_b = pixel_f
        pixel_f = object_
    else:
        pixel_b = ' '

    # If the front block has a transparent bg
    if blocks[pixel_f]['colours']['bg'] is None:

        # ...and the back block has a transparent bg
        bg = blocks[pixel_b]['colours']['bg']
        if bg is None:
            # ...bg is sky
            bg = sky(x, y, tick, sun, lights)

        # if there is no object, use the fg colour
        fg = obj_colour
        if fg is None:
            fg = blocks[pixel_f]['colours']['fg']

        return colour_str(
            blocks[pixel_f]['char'],
            bg = bg,
            fg = fg,
            style = blocks[pixel_f]['colours']['style']
        )

    else: # The block was coloured on startup
        return blocks[pixel_f]['char']


def sun(time, width):
    """ Returns position of sun """

    sun_r = width / 2

    # Set i to +1 for night and -1 for day
    i = -2 * (cos(time) > 0) + 1
    x = int(sun_r * i * sin(time) + sun_r + 1)
    y = int(sun_r * i * cos(time) + sun_y)

    return x, y


# Distance from l['center'] in terms of l['radius']
lit = lambda x, y, l: ((((x-l['x'])**2) / l['radius']**2) +
                       (((y-l['y'])**2) / (l['radius']/2)**2))


def sky(x, y, time, sun, lights):
    """ Returns the sky colour. """

    if sun[0] in [x, x+1] and sun[1] == y:
        # Sun pixel
        return YELLOW if cos(time) > 0 else WHITE
    else:
        # Sky pixel
        day, night = (0,.4,1), (0,0,.2)
        shade = (cos(time) + 1) / 2
        sky_colour = lerp_n(night, shade, day)

        if lights:
            distance = min(min(map(lambda l: lit(x, y, l), lights)), 1)
            # TODO: Shouldn't need to do max with sky_colour...
            return max(rgb(*lerp_n(day, distance, sky_colour)), rgb(*sky_colour))
        else:
            return rgb(*sky_colour)


def lerp(a, s, b):
  return a * (1 - s) + (b * s)


def lerp_n(a, s, b):
    return tuple(lerp(a[i], s, b[i]) for i in range(min(len(a), len(b))))


def get_lights(_map, start_x, blocks):
    lights = []

    for x, slice_ in _map.items():
        # Get the lights and their y positions in this slice
        slice_lights = filter(lambda pixel: blocks[pixel[1]].get('light'),
            zip(range(len(slice_)), slice_)) # [(0, ' '), (1, '~'), ...]

        # Convert light pixels to light objects
        lights.extend(map(
            lambda pixel: {
                'radius': blocks[pixel[1]]['light'],
                'x': x-start_x,
                'y': pixel[0]
            },
            slice_lights
        ))

    return lights


def render_grid(title, selected, grid, blocks, max_height, sel=None):
    h, v, tl, t, tr, l, m, r, bl, b, br = \
        supported_chars('─│╭┬╮├┼┤╰┴╯', '─│┌┬┐├┼┤└┴┘', '-|+++++++++')

    max_height = int((max_height-2) / 2) # -2 for title, bottom

    # Figure out offset
    if sel:
        bottom_pad = 2

        offset = sel - max(
            min(sel, max_height - bottom_pad - 1), # Beginning and middle
            sel + min(0, max_height - len(grid)) # End positions
        )
    else:
        offset = 0

    # Find maximum length of the num column.
    max_n_w = len(str(max(map(lambda s: s['num'], grid)))) if len(grid) else 1

    # Figure out number of trailing spaces to make the grid same width as the title.
    #     |   block    |         num          |
    top = tl + (h*3) + t + (h*(max_n_w+2)) + tr
    max_w = max(len(top), len(title))
    trailing = ' ' * (max_w - len(top))

    out = []
    out.append(bold(title, selected) + ' ' * (max_w - len(title)))
    out.append(top + trailing)

    for c, slot in enumerate(grid[offset:offset+max_height]):
        i = c + offset

        if slot is not None:
            block_char = blocks[slot['block']]['char']
            num = slot['num']
        else:
            block_char, num = ' ', ''

        colour = blocks[slot['block']]['colours']
        if colour['bg'] is None:
            block_char = colour_str(
                block_char,
                fg=colour['fg'],
                bg=None,
                style=colour['style']
            )

        # Have to do the padding before colour because the colour
        #   messes with the char count. (The block will always be 1 char wide.)
        num = '{:{max}}'.format(num, max=max_n_w)

        out.append('{v} {b} {v} {n} {v}{trail}'.format(
            b=block_char,
            n=colour_str(num, bg=RED) if selected and i == sel else num,
            v=v,
            trail=trailing
        ))

        if not (c == max_height - 1 or i == len(grid) - 1):
            out.append(l + (h*3) + m + (h*(max_n_w+2)) + r + trailing)

    out.append(bl + (h*3) + b + (h*(max_n_w+2)) + br + trailing)
    return out


def render_grids(grids, x, max_height):
    """
        Prints out the grids on the right side of the game.
    """

    # Sort out grids
    # Gets row from grid if it exists, else pads with ' '
    get_row = lambda g, y: g[y] if y < len(g) else ' ' * len(uncolour_str(g[0]))

    merged_grids = []
    for row in grids:
        for y in range(max(map(len, row))):
            merged_grids.append(' '.join(map(lambda g: get_row(g, y), row)))

    merged_grids.extend('' for _ in range(max_height - len(merged_grids)))

    return ''.join(
        POS_STR(x, y, ' ' + row + CLS_END_LN)
            for y, row in enumerate(merged_grids)
    )


def gen_blocks():
    # Convert the characters to their coloured form
    for key, block in blocks.items():

        # Get supported version of block char
        blocks[key]['char'] = supported_chars(*block['char'])

        # If bg is transparent, it must be coloured at runtime.
        if blocks[key]['colours']['bg'] is not None:
            blocks[key]['char'] = colour_str(
                blocks[key]['char'],
                block['colours']['fg'],
                block['colours']['bg'],
                block['colours']['style']
            )

    return blocks
