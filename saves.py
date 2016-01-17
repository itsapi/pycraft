import os
import json
import random

from shutil import rmtree

from terrain import world_gen
from console import log


default_meta = {
    'name': 'Untitled',
    'seed': '',
    'spawn': 0,
    'tick': 0,
    'players': {}
}

default_player = {
    'player_x': int(os.getenv('PYCRAFT_START_X') or 0),
    'player_y': 1,
    'inv': []
}

SAVES_DIR = 'saves'
CHUNK_EXT = '.chunk'
CHUNK_SIZE = world_gen['chunk_size'] * (world_gen['height'] + 1)


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


def get_meta(save):
    with open(meta_path(save)) as f:
        data = json.load(f)

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


def save_meta(save, meta):
    # Save meta file
    with open(meta_path(save), 'w') as f:
        json.dump(meta, f)


def chunk_file_name(save, chunk_n):
    return save_path(save, str(chunk_n) + CHUNK_EXT)


def load_chunk(save, chunk_n):
    map_ = {}
    chunk_pos = chunk_n * world_gen['chunk_size']

    try:
        with open(chunk_file_name(save, chunk_n)) as data:
            for d_pos, slice_ in enumerate(data):

                # Truncate to correct size
                slice_ = slice_[:world_gen['height']]

                height_error = world_gen['height'] - len(slice_)
                if not height_error == 0:
                    # Extend slice height
                    slice_ = (' ' * height_error) + slice_

                map_[str(chunk_pos + d_pos)] = list(slice_)

    except FileNotFoundError:
        pass

    return map_


def save_chunk(save, chunk_n, chunk):
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

            file_.seek(int(rel_pos) * (world_gen['height'] + 1))
            file_.write(''.join(slice_) + '\n')


def save_slices(save, new_slices):
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
        save_chunk(save, chunk_pos, chunk)


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


def get_global_meta():
    try:
        with open('meta.json') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    return data


def save_global_meta(meta):
    with open('meta.json', 'w') as f:
        json.dump(meta, f)


def add_server(meta, server):
    meta['servers'] = meta.get('servers', [])
    meta['servers'].append(server)
    save_global_meta(meta)


def delete_server(meta, server):
    meta['servers'].remove(server)
    save_global_meta(meta)
