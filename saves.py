import os
import json
import random

from shutil import rmtree

from terrain import world_gen


default_meta = {
    'name': 'Untitled',
    'seed': lambda: hash(random.random()),
    'spawn': 0,
    'player_x': 0,
    'player_y': 1,
    'inv': [],
    'tick': 0
}

default_global_meta = {
    'settings': {
        'colours': True,
        'fancy_lights': True
    }
}

SAVES_DIR = 'saves'
CHUNK_EXT = '.chunk'
SLICE_SEP = '<sep>'


save_path = lambda save, filename='': os.path.join(SAVES_DIR, save, filename)
meta_path = lambda save: save_path(save, 'meta.json')
chunk_num = lambda x: int(x) // world_gen['chunk_size']


def check_map_dir():
    if not os.path.isdir(SAVES_DIR): os.mkdir(SAVES_DIR)


def new_save(meta):
    meta = check_meta(meta)

    # Find unique dir name
    save = meta['name'].lower()

    save = ''.join(c if c.isalpha() else '_' for c in save)

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


def load_save(save):
    meta = get_meta(save)

    try:
        map_ = check_map(get_map(save), meta)
    except FileNotFoundError:
        map_ = {}

    save_map(save, map_)

    return meta, map_, save


def get_map(save):
    map_ = []

    chunks = (file_ for file_ in os.listdir(save_path(save))
              if file_.endswith(CHUNK_EXT))
    for chunk in chunks:

        with open(save_path(save, chunk)) as f:
            data = f.readlines()

        map_ += data

    return map_


def check_map(data, meta):
    map_ = parse_slices(data)

    for key, slice_ in map_.items():
        if not len(slice_) == world_gen['height']:

            if len(slice_) < world_gen['height']:
                # Extend slice height
                slice_ = [' '] * (world_gen['height'] - len(slice_)) + slice_
            elif len(slice_) > world_gen['height']:
                # Truncate slice height
                slice_ = slice_[len(slice_) - world_gen['height']:]

            map_[key] = slice_

    return map_


def parse_slices(data):
    slices = {}

    for line in data:
        # Parses map file
        parts = line.split(SLICE_SEP)
        key, slice_ = int(parts[0]), parts[1]
        slice_ = list(slice_)

        # Removes new line char if it exists
        slices[key] = slice_ if not slice_[-1] == '\n' else slice_[:-1]

    return slices


def save_map(save, slices):
    # Group slices by chunk
    chunks = {}
    for pos, slice_ in slices.items():
        try:
            chunks[chunk_num(pos)].update({pos: slice_})
        except KeyError:
            chunks[chunk_num(pos)] = {pos: slice_}

    # Update chunk files
    for num, chunk in chunks.items():
        # Update slices in chunk file with new slices
        try:
            with open(save_path(save, str(num) + CHUNK_EXT)) as f:
                slices = parse_slices(f.readlines())
        except (OSError, IOError):
            slices = {}
        slices.update(chunk)

        # Write slices back to file
        with open(save_path(save, str(num) + CHUNK_EXT), 'w') as f:
            for pos, slice_ in slices.items():
                f.write(str(pos) + SLICE_SEP + ''.join(slice_) + '\n')


def list_saves():
    return [(save, get_meta(save)) for save in os.listdir(SAVES_DIR)
        if os.path.isdir(save_path(save))]


def check_meta(meta):
    return set_defaults(meta, default_meta)


def save_meta(save, meta):
    # Save meta file
    save_json(meta_path(save), meta)


def load_global_meta():
    return load_meta('meta.json', default_global_meta)


def get_meta(save):
    return load_meta(meta_path(save), default_meta)


def save_json(path, meta):
    with open(path, 'w') as f:
        json.dump(meta, f)


def load_meta(path, default):
    try:
        with open(path) as f:
            meta = json.load(f)
    except FileNotFoundError:
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
