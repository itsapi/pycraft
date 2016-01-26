from math import cos, sin, sqrt, modf

from colours import *
from console import *
from data import world_gen, blocks


sun_y = world_gen['height'] - world_gen['ground_height']
max_light = max(map(lambda b: b.get('light', 0), blocks.values()))

FANCY_LIGHTING = True


def render_map(map_, objects, blocks, bk_objects, lights, tick, last_frame):
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

            pixel_out = calc_pixel(x, y, pixel, objects, blocks, bk_objects, lights, tick)
            this_frame[-1].append(pixel_out)

            try:
                if not last_frame[y][x] == pixel_out:
                    # Changed
                    diff += POS_STR(x, y, pixel_out)
            except IndexError:
                # Doesn't exist
                diff += POS_STR(x, y, pixel_out)

    return diff, this_frame


def obj_pixel(x, y, objects, blocks):

    for object_ in objects:
        if object_['x'] == x and object_['y'] == y:

            # Objects can override their block colour
            colour = object_.get('colour', blocks[object_['char']]['colours']['fg'])

            return object_['char'], colour

    return None, None


def calc_pixel(x, y, pixel_f, objects, blocks, bk_objects, lights, tick):

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
            bg = sky(x, y, tick, bk_objects, lights)

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


def bk_objects(time, width):
    """ Returns objects for rendering to the background """

    objects = []

    sun_r = width / 2
    day = cos(time) > 0

    # Set i to +1 for night and -1 for day
    i = -2 * day + 1
    x = int(sun_r * i * sin(time) + sun_r + 1)
    y = int(sun_r * i * cos(time) + sun_y)

    obj = {
        'x': x,
        'y': y,
        'width': 2,
        'height': 1,
        'colour': world_gen['sun_colour'] if day else world_gen['moon_colour']
    }

    if FANCY_LIGHTING:
        obj['light_colour'] = world_gen['sun_light_colour'] if day else world_gen['moon_light_colour'],
        obj['light_radius'] = world_gen['sun_light_radius']

    objects.append(obj)

    return objects


# Distance from l['center'] in terms of l['radius']
lit = lambda x, y, l: min((((x-l['x'])**2) / l['radius']**2) +
                          (((y-l['y'])**2) / (l['radius']/2)**2), 1)


def sky(x, y, time, bk_objects, lights):
    """ Returns the sky colour. """

    for obj in bk_objects:
        if obj['x'] in range(x, x+obj['width']) and obj['y'] in range(y, y+obj['height']):
            return rgb(*obj['colour'])

    shade = (cos(time) + 1) / 2

    if FANCY_LIGHTING:
        # Sky pixel
        sky_colour = lerp_n(rgb_to_hsv(world_gen['night_colour']), shade, rgb_to_hsv(world_gen['day_colour']))

        # Get all lights which effect this pixel
        pixel_lights = filter(lambda l: l[1] < 1, map(lambda l: (l['colour'], lit(x, y, l)), lights))

        # Calculate light level for each light source
        light_levels = map(lambda l: lerp_n(rgb_to_hsv(l[0]), l[1], sky_colour), pixel_lights)

        # Get brightest light
        light = max(light_levels, key=lambda l: l[2], default=sky_colour)

        pixel_colour = hsv_to_rgb(light)

    else:

        if shade > .5 or any(map(lambda l: lit(x, y, l) < 1, lights)):
            pixel_colour = CYAN#world_gen['day_colour']
        else:
            pixel_colour = BLUE#world_gen['night_colour']

    return pixel_colour
    # return rgb(*pixel_colour)


def lerp(a, s, b):
  return a * (1 - s) + (b * s)


def lerp_n(a, s, b):
    return tuple(lerp(a[i], s, b[i]) for i in range(min(len(a), len(b))))


def rgb_to_hsv(colour):
    r, g, b = colour

    min_c = min(*colour);
    max_c = max(*colour);
    v = max_c;

    delta = max_c - min_c;

    if not max_c == 0:
        s = delta / max_c;

        if delta == 0:
            h = 0
        elif r == max_c:
            # Between yellow & magenta
            h = (g - b) / delta
        elif g == max_c:
            # Between cyan & yellow
            h = 2 + (b - r) / delta
        else:
            # Between magenta & cyan
            h = 4 + (r - g) / delta

        h *= 60

        if h < 0:
            h += 360

    else:
        s = 0;
        h = -1;

    return h, s, v


def hsv_to_rgb(colour):
    h, s, v = colour

    if s == 0:
        # Grey
        return (v, v, v)

    # Sector 0 to 5
    h /= 60

    i = int(h);

    # Factorial part of h
    f = h - i

    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    return {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q)
    }[i]


def get_lights(_map, start_x, blocks, bk_objects):
    # Give background objects light
    lights = list(map(lambda obj: {
        'radius': obj['light_radius'],
        'x': obj['x'],
        'y': obj['y'],
        'colour': obj['light_colour']
    }, filter(lambda obj: obj.get('light_radius'), bk_objects)))

    # Give blocks light
    for x, slice_ in _map.items():
        # Get the lights and their y positions in this slice
        slice_lights = filter(lambda pixel: blocks[pixel[1]].get('light_radius'),
            zip(range(len(slice_)), slice_)) # [(0, ' '), (1, '~'), ...]

        # Convert light pixels to light objects
        lights.extend(map(
            lambda pixel: {
                'radius': blocks[pixel[1]]['light_radius'],
                'x': x-start_x,
                'y': pixel[0],
                'colour': blocks[pixel[1]].get('light_colour', (1,1,1))
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
