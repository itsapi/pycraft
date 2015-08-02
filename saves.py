import os
import json
import random

from shutil import rmtree

from terrain import world_gen
from console import debug


default_meta = {
    'name': 'Untitled',
    'seed': '',
    'spawn': 0,
    'tick': 0,
    'players': {}
}

default_player = {
    'player_x': 0,
    'player_y': 1,
    'inv': []
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

    bad_chars = (' /\\!"£$%^*()=.?><\'@#~;:]}[{|`¬')
    for bad_char in bad_chars:
        save = save.replace(bad_char, '_')

    while os.path.isdir(save_path(save)):
        save += '-'
    os.mkdir(save_path(save))

    save_meta(save, meta)
    return save


def delete_save(save):
    rmtree(save_path(save))


def load_player(name, meta):
    if name not in meta['players']:
        meta['players'][name] = default_player
    return meta


def load_meta(save):
    try:
        meta = check_meta(get_meta(save))
    except FileNotFoundError:
        meta = default_meta

    save_meta(save, meta)
    return meta


def load_chunk(save, chunk):
    try:
        map_ = check_map(get_chunk(save, chunk))
    except FileNotFoundError:
        map_ = {}

    save_map(save, map_)
    return map_


def get_meta(save):
    with open(meta_path(save)) as f:
        data = json.load(f)

    return data


def get_chunk(save, chunk):
    data = []

    chunk_file = save_path(save, str(chunk) + CHUNK_EXT)

    if os.path.isfile(chunk_file):
        with open(chunk_file) as f:
            data = f.readlines()

    return data


def check_meta(meta):
    # Create meta items if needed
    for key, default in default_meta.items():
        try:
            meta[key]
        except KeyError:
            meta[key] = default

    if not meta['seed']:
        meta['seed'] = hash(random.random())

    return meta


def check_map(data):
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
        key, slice_ = line.split(SLICE_SEP)
        slice_ = list(slice_)

        # Removes new line char if it exists
        slices[key] = slice_ if not slice_[-1] == '\n' else slice_[:-1]

    return slices


def save_meta(save, meta):
    # Save meta file
    with open(meta_path(save), 'w') as f:
        json.dump(meta, f)


def save_map(save, new_slices):
    # Group slices by chunk
    chunks = {}
    for pos, slice_ in new_slices.items():
        try:
            chunks[chunk_num(pos)].update({pos: slice_})
        except KeyError:
            chunks[chunk_num(pos)] = {pos: slice_}

    debug('saving slices', new_slices.keys())
    debug('saving chunks', chunks.keys())

    # Update chunk files
    for num, chunk in chunks.items():
        chunk_file = save_path(save, str(num) + CHUNK_EXT)

        # Update slices in chunk file with new slices
        try:
            with open(chunk_file) as f:
                slices = parse_slices(f.readlines())
        except (OSError, IOError):
            slices = {}
        slices.update(chunk)

        # Write slices back to file
        with open(chunk_file, 'w') as f:
            for pos, slice_ in slices.items():
                f.write(str(pos) + SLICE_SEP + ''.join(slice_) + '\n')


def set_blocks(map_, blocks):
    new_slices = {}

    for x, col in blocks.items():
        for y, block in col.items():
            try:
                new_slices[str(x)] = map_[str(x)]
                map_[str(x)][int(y)] = new_slices[str(x)][int(y)] = block
            except KeyError:
                pass

    return map_, new_slices


def list_saves():
    return [(save, get_meta(save)) for save in os.listdir(SAVES_DIR)
        if os.path.isdir(save_path(save))]
