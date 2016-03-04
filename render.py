from math import pi, cos, sin, sqrt, modf, radians

from colours import *
from console import *
from data import lighting, world_gen, blocks, timings
from terrain import is_solid


sun_y = world_gen['height'] - world_gen['ground_height']
max_light = max(map(lambda b: b.get('light_radius', 0), blocks.values()))


def in_circle(test_x, test_y, x, y, r):
    return circle_dist(test_x, test_y, x, y, r) < 1


def circle_dist(test_x, test_y, x, y, r):
    return ( ( ((test_x - x) ** 2) /  r    ** 2) +
             ( ((test_y - y) ** 2) / (r/2) ** 2) )


lit = lambda x, y, p: min(circle_dist(x, y, p['x'], p['y'], p['radius']), 1)


def render_map(map_, slice_heights, edges, edges_y, objects, bk_objects, sky_colour, day, lights, last_frame, fancy_lights):
    """
        Prints out a frame of the game.

        Takes:
        - map_: a 2D list of blocks.
        - edges: the range to display
        - objects: a list of dictionaries:
            {'x': int, 'y': int, 'char': block}
        - blocks: the main dictionary describing the blocks in the game.
        - bk_objects: list of objects to be displayed in the background:
            {'x': int, 'y': int, 'colour': tuple[3], 'light_colour': tuple[3], 'light_radius': tuple[3]}
        - sky_colour: the colour of the sky
        - lights: a list of light sources:
            {'x': int, 'y': int, 'radius': int, 'colour': tuple[3]}
        - last_frame: dictionary of all blocks displayed in the last frame
        - fancy_lights: bool
    """

    diff = ''
    this_frame = {}

    for world_x, column in map_.items():
        if world_x in range(*edges):

            x = world_x - edges[0]

            for world_y, pixel in enumerate(column):
                if world_y in range(*edges_y):

                    y = world_y - edges_y[0]

                    pixel_out = calc_pixel(x, y, world_x, world_y, edges[0], map_, slice_heights, pixel, objects, bk_objects, sky_colour, day, lights, fancy_lights)

                    if DEBUG and y == 1 and world_x % world_gen['chunk_size'] == 0:
                        pixel_out = colour_str('*', bg=TERM_RED, fg=TERM_YELLOW)

                    this_frame[x, y] = pixel_out

                    try:
                        if not last_frame[x, y] == pixel_out:
                            # Changed
                            diff += POS_STR(x, y, pixel_out)
                    except KeyError:
                        # Doesn't exist
                        diff += POS_STR(x, y, pixel_out)

    return diff, this_frame


def obj_pixel(x, y, objects):

    for object_ in objects:
        if object_['x'] == x and object_['y'] == y:

            # Objects can override their block colour
            colour = object_.get('colour', blocks[object_['char']]['colours']['fg'])

            return object_['char'], colour

    return None, None


def calc_pixel(x, y, world_x, world_y, world_screen_x, map_, slice_heights, pixel_f, objects, bk_objects, sky_colour, day, lights, fancy_lights):

    # If the front block has a bg
    if blocks[pixel_f]['colours']['bg'] is not None:
        bg = get_block_light(x, world_y, world_screen_x, map_, slice_heights, lights, day, blocks[pixel_f]['colours']['bg'], fancy_lights)
    else:
        bg = sky(x, world_y, world_screen_x, map_, slice_heights, bk_objects, sky_colour, lights, fancy_lights)

    # Get any object
    object_char, obj_colour = obj_pixel(x, world_y, objects)

    if object_char:
        char = object_char
        fg = obj_colour
    else:
        char = get_char(world_x, world_y, map_, pixel_f)

        if blocks[pixel_f]['colours']['fg'] is not None:
            fg = get_block_light(x, world_y, world_screen_x, map_, slice_heights, lights, day, blocks[pixel_f]['colours']['fg'], fancy_lights)
        else:
            fg = None

    fg_colour = rgb(*fg) if fg is not None else None
    bg_colour = rgb(*bg) if bg is not None else None

    return colour_str(
        char,
        bg = bg_colour,
        fg = fg_colour,
        style = blocks[pixel_f]['colours']['style']
    )


def get_block(x, y, map_):
    try:
        return map_[x][y]
    except (KeyError, IndexError):
        return None


def get_char(x, y, map_, pixel):
    left = get_block(x-1, y, map_)
    right = get_block(x+1, y, map_)
    below = get_block(x, y+1, map_)

    char = blocks[pixel]['char']

    if below is None or not is_solid(below):

        if left is not None and is_solid(left) and 'char_left' in blocks[pixel]:
            char = blocks[pixel]['char_left']

        elif right is not None and is_solid(right) and 'char_right' in blocks[pixel]:
            char = blocks[pixel]['char_right']

    return char


def bk_objects(ticks, width, fancy_lights):
    """ Returns objects for rendering to the background """

    objects = []

    seconds = ticks / timings['tps']
    day_time = (seconds / timings['day_length']) % 1
    day = day_time < .5

    day_angle = day_time * 2 * pi
    sun_angle = day_angle % pi

    sun_r = width / 2

    x = int(sun_r * cos(sun_angle % pi) + width/2 + 1)
    y = int(sun_y - sun_r * sin(sun_angle % pi))

    light_type = 'sun' if day else 'moon'

    # Sun/moon
    obj = {
        'x': x,
        'y': y,
        'z': -1 if day else -2,
        'width': 2,
        'height': 1,
        'colour': lighting[light_type + '_colour']
    }

    shade = (sin(day_angle) + 1)/2

    if fancy_lights:
        sky_colour = lerp_n(rgb_to_hsv(lighting['night_colour']), shade, rgb_to_hsv(lighting['day_colour']))

        obj['light_colour'] = lighting[light_type + '_light_colour']
        obj['light_radius'] = lighting[light_type + '_light_radius'] * sin(sun_angle)
    else:
        sky_colour = CYAN if day else BLUE

    objects.append(obj)

    return objects, sky_colour, shade


def get_block_lights(x, y, lights):
    # Get all lights which affect this pixel
    for l in lights:
        l['distance'] = lit(x, y, l)
    return filter(lambda l: l['distance'] < 1, lights)


def get_light_colour(x, y, world_x, map_, slice_heights, lights, colour_behind, fancy_lights):
    # return colour_behind
    if (world_gen['height'] - y) < slice_heights[world_x + x]:

        light = (.1,.1,.1)
        if fancy_lights:
            block_lightness = get_block_lightness(x, y, world_x, map_, slice_heights, lights)
            light = [(b + block_lightness) / 2 for b in light]

    else:

        if fancy_lights:
            pixel_lights = get_block_lights(x, y, lights)

            # Calculate light level for each light source
            light_levels = [hsv_to_rgb(lerp_n(rgb_to_hsv(l['colour']), l['distance'], colour_behind)) for l in pixel_lights]

            # Get brightest light
            if light_levels:
                light = max(map(lambda l: round_to_palette(*l), light_levels), key=lightness)
            else:
                light = hsv_to_rgb(colour_behind)

        else:

            light = CYAN if any(map(lambda l: lit(x, y, l) < 1, lights)) else colour_behind

    return light


def light_mask(x, y, map_, slice_heights):
    if is_solid(map_[x][y]) or (world_gen['height'] - y) < slice_heights[x]:
        z = 0
    else:
        z = -1
    return z


def get_block_lightness(x, y, world_x, map_, slice_heights, lights):
    block_lights = get_block_lights(x, y, lights)

    # If the light is not hidden by the mask
    block_lights = filter(lambda l: l['z'] >= light_mask(world_x + l['x'], l['y'], map_, slice_heights), block_lights)

    # Multiply the distance from the source by the lightness of the source colour.
    block_lights_lightness = map(lambda l: l['distance'] * lightness(l['colour']), block_lights)

    try:
        block_lightness = 1 - min(block_lights_lightness)
    except ValueError:
        block_lightness = 0

    return block_lightness


def get_block_light(x, y, world_x, map_, slice_heights, lights, day, block_colour, fancy_lights):
    lit_block = block_colour

    if fancy_lights:
        block_lightness = get_block_lightness(x, y, world_x, map_, slice_heights, lights)

        d_ground_height = slice_heights[world_x+x] - (world_gen['height'] - y)
        v = lerp(day, min(1, max(0, d_ground_height/3)), 0)
        hsv = rgb_to_hsv(lit_block)
        lit_block = hsv_to_rgb((hsv[0], hsv[1], lerp(0, max(v, block_lightness), hsv[2])))

    return lit_block


def sky(x, y, world_x, map_, slice_heights, bk_objects, sky_colour, lights, fancy_lights):
    """ Returns the sky colour. """

    bk_objects = filter(lambda l: l['z'] >= light_mask(world_x + l['x'], l['y'], map_, slice_heights), bk_objects)

    for obj in bk_objects:
        if obj['x'] in range(x, x+obj['width']) and obj['y'] in range(y, y+obj['height']):
            return obj['colour']

    return get_light_colour(x, y, world_x, map_, slice_heights, lights, sky_colour, fancy_lights)


def lerp(a, s, b):
  return a * (1 - s) + (b * s)


def lerp_n(a, s, b):
    return tuple(lerp(a[i], s, b[i]) for i in range(min(len(a), len(b))))


def rgb_to_hsv(colour):
    r, g, b = colour

    min_c = min(*colour)
    max_c = max(*colour)
    v = max_c

    delta = max_c - min_c

    if not max_c == 0:
        s = delta / max_c

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
        s = 0
        h = -1

    return h, s, v


def hsv_to_rgb(colour):
    h, s, v = colour

    if s == 0:
        # Grey
        return (v, v, v)

    # Sector 0 to 5
    h /= 60

    i = int(h)

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


def get_lights(_map, start_x, bk_objects):
    # Give background objects light
    lights = list(map(lambda obj: {
        'radius': obj['light_radius'],
        'x': obj['x'],
        'y': obj['y'],
        'z': obj['z'],
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
                'z': 0,
                'colour': blocks[pixel[1]].get('light_colour', (1,1,1))
            },
            slice_lights
        ))

    return lights


def render_grid(title, selected, grid, max_height, sel=None):
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

        block_char = blocks[slot['block']]['char']
        num = slot['num']

        colour = blocks[slot['block']]['colours']
        block_char = colour_str(
            block_char,
            fg=rgb(*colour['fg']) if colour['fg'] is not None else None,
            bg=rgb(*colour['bg']) if colour['bg'] is not None else None,
            style=colour['style']
        )

        # Have to do the padding before colour because the colour
        #   messes with the char count. (The block will always be 1 char wide.)
        num = '{:{max}}'.format(num, max=max_n_w)

        out.append('{v} {b} {v} {n} {v}{trail}'.format(
            b=block_char,
            n=colour_str(num, bg=rgb(*RED)) if selected and i == sel else num,
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
