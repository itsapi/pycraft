from math import cos, sin

from colors import *
from console import CLS, CLS_END, CLS_END_LN, REDRAW, supported_chars
from data import world_gen, blocks


sun_y = world_gen['height'] - world_gen['ground_height']

max_light = max(map(lambda b: b.get('light', 0), blocks.values()))


def render_map(map_, objects, grids, blocks, sun, lights, tick):
    """
        Prints out a frame of the game.

        Takes:
        - map_: a 2D list of blocks.
        - objects: a list of dictionaries:
            {'x': int, 'y': int, 'char': block}
        - grids: a list of 2D lists of chars to make up the inventory on
            the right of the game.
        - blocks: the main dictionary describing the blocks in the game.
        - sun: (x, y) position of the sun.
        - lights: a list of light sources:
            {'x': int, 'y': int, 'radius': int}
        - tick: the game time.
    """

    # Sort out grids
    merged_grids = []
    for row in grids:
        for y in range(max(map(len, row))):
            merged_grids.append(' '.join(map(lambda g: g[y] if y < len(g) else ' ' * len(g[0]), row)))

    # Sorts the dict as a list by pos
    map_ = list(map_.items())
    map_.sort(key=lambda item: int(item[0]))

    # map_ = [[0, '##  '],
    #         [1, '### '],
    #         [2, '##  ']]

    # Seperates the pos and data
    map_ = tuple(zip(*map_))[1]

    # Orientates the data
    map_ = zip(*map_)

    # Output the map
    out = ''
    for y, row in enumerate(map_):
        for x, pixel in enumerate(row):
            out += calc_pixel(x, y, pixel, objects, blocks, sun, lights, tick)

        # Grids
        if y < len(merged_grids):
            out += ' ' + merged_grids[y]

        out += CLS_END_LN + '\n'

    print(REDRAW + out + CLS_END)


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

        return colorStr(
            blocks[pixel_f]['char'],
            bg = bg,
            fg = obj_colour or blocks[pixel_f]['colours']['fg'],
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


# Checks if a point is within a lights range.
lit = lambda x, y, l: (( ((x-l['x']) ** 2) /  l['radius']    ** 2)
                     + ( ((y-l['y']) ** 2) / (l['radius']/2) ** 2) < 1)

def sky(x, y, time, sun, lights):
    """ Returns the sky colour. """

    day = cos(time) > 0

    if sun[0] in [x, x+1] and sun[1] == y:
        # Sun pixel
        if day:
            return YELLOW
        else:
            return WHITE
    else:
        # Sky pixel
        if day or any(map(lambda l: lit(x, y, l), lights)):
            return CYAN
        else:
            return BLUE


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


def gen_blocks():
    # Convert the characters to their coloured form
    for key, block in blocks.items():

        # Get supported version of block char
        blocks[key]['char'] = supported_chars(*block['char'])

        # If bg is transparent, it must be coloured at runtime.
        if blocks[key]['colours']['bg'] is not None:
            blocks[key]['char'] = colorStr(
                blocks[key]['char'],
                block['colours']['fg'],
                block['colours']['bg'],
                block['colours']['style']
            )

    return blocks
