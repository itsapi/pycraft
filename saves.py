import os
import json
import random

from shutil import rmtree

from terrain import world_gen
from console import log
from data import timings


default_meta = {
    'name': 'Untitled',
    'seed': lambda: hash(random.random()),
    'spawn': 0,
    'tick': timings['tick'],
    'players': {}
}

default_global_meta = {}

default_settings = {
    'name': None,
    'colours': True,
    'fancy_lights': True,
    'neopixels': True,
    'terminal_output': True,
    'gravity': False,
    'flight': False,
    'width': 40,
    'height': 30
}

default_player = {
    'player_x': int(os.getenv('PYCRAFT_START_X') or 0),
    'player_y': 1,
    'inv': []
}

SAVES_DIR = 'saves'
CHUNK_EXT = '.chunk'
SAVE_LINE_LENGTH = world_gen['height'] + 3 + 1  # + slice_height + newline
CHUNK_SIZE = world_gen['chunk_size'] * SAVE_LINE_LENGTH


save_path = lambda save, filename='': os.path.join(SAVES_DIR, save, filename)
meta_path = lambda save: save_path(save, 'meta.json')
chunk_num = lambda x: int(x) // world_gen['chunk_size']


def check_map_dir():
    if not os.path.isdir(SAVES_DIR): os.mkdir(SAVES_DIR)


def new_save(meta):
    meta = check_meta(meta)

    # Find unique dir name
    save = meta['name'].lower()

    save = ''.join(c if c.isalnum() else '_' for c in save)

    while os.path.isdir(save_path(save)):
        save += '-'

    try:
        os.mkdir(save_path(save))
    except OSError:
        save = None
    else:
        save_meta(save, meta)
    finally:
        return save


def delete_save(save):
    rmtree(save_path(save))


def load_player(name, meta):
    if name not in meta['players']:
        meta['players'][name] = {}
        meta['players'][name].update(default_player)
    return meta


def chunk_file_name(save, chunk_n):
    return save_path(save, str(chunk_n) + CHUNK_EXT)


def load_chunk(save, chunk_n):
    map_ = {}
    slice_heights = {}
    chunk_pos = chunk_n * world_gen['chunk_size']

    try:
        with open(chunk_file_name(save, chunk_n)) as data:
            for d_pos, line in enumerate(data):
                abs_pos = chunk_pos + d_pos

                # Truncate to correct size
                slice_ = line[:world_gen['height']]

                height_error = world_gen['height'] - len(slice_)
                if not height_error == 0:
                    # Extend slice height
                    slice_ = (' ' * height_error) + slice_

                map_[abs_pos] = list(slice_)

                try:
                    slice_heights[abs_pos] = int(line[world_gen['height']:])
                except ValueError:
                    slice_heights[abs_pos] = world_gen['ground_height']

    except IOError:
        pass

    return map_, slice_heights


def save_chunk(save, chunk_n, chunk, slice_heights):
    """ Updates slices within one chunk. """

    filename = chunk_file_name(save, chunk_n)
    if os.path.isfile(filename):
        mode = 'r+'
    else:
        mode = 'w'

    with open(filename, mode) as file_:

        file_.truncate(CHUNK_SIZE)
        for pos, slice_ in chunk.items():
            rel_pos = int(pos) % world_gen['chunk_size']

            file_.seek(int(rel_pos) * SAVE_LINE_LENGTH)
            file_.write(''.join(slice_) + str(slice_heights[pos])[:3].zfill(3) + '\n')


def save_slices(save, new_slices, slice_heights):
    """ Updates slices anywhere in the world. """

    # Group slices by chunk
    chunks = {}
    for pos, slice_ in new_slices.items():
        chunk_pos = chunk_num(pos)

        try:
            chunks[chunk_pos].update({pos: slice_})
        except KeyError:
            chunks[chunk_pos] = {pos: slice_}

    log('saving slices', new_slices.keys())
    log('saving chunks', chunks.keys())

    # Update chunk files
    for chunk_pos, chunk in chunks.items():
        save_chunk(save, chunk_pos, chunk, slice_heights)


def set_blocks(map_, blocks):
    new_slices = {}

    for x, col in blocks.items():
        for y, block in col.items():
            try:
                new_slices[int(x)] = map_[int(x)]
                map_[int(x)][int(y)] = new_slices[int(x)][int(y)] = block
            except KeyError:
                pass

    return map_, new_slices


def list_saves():
    return [(save, get_meta(save)) for save in os.listdir(SAVES_DIR)
            if os.path.isdir(save_path(save))]


def add_server(meta, server):
    meta['servers'] = meta.get('servers', [])
    meta['servers'].append(server)
    save_global_meta(meta)


def delete_server(meta, server):
    meta['servers'].remove(server)
    save_global_meta(meta)


def check_meta(meta):
    return set_defaults(meta, default_meta)


def save_global_meta(meta):
    save_json('meta.json', meta)


def save_settings(meta):
    save_json('settings.json', meta)


def save_meta(save, meta):
    save_json(meta_path(save), meta)


def get_global_meta():
    return load_meta('meta.json', default_global_meta)


def get_settings():
    return load_meta('settings.json', default_settings)


def get_meta(save):
    return load_meta(meta_path(save), default_meta)


def save_json(path, meta):
    with open(path, 'w') as f:
        json.dump(meta, f)


def load_meta(path, default):
    try:
        with open(path) as f:
            meta = json.load(f)
    except IOError:
        meta = default
    else:
        set_defaults(meta, default)

    save_json(path, meta)
    return meta


def set_defaults(options, defaults):
    for key, default in defaults.items():
        if key not in options:
            if callable(default):
                options[key] = default()
            else:
                options[key] = default

        if isinstance(default, dict):
            options[key] = set_defaults(options[key], default)

    return options
