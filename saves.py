import os
import json


default_meta = {
    'name': 'Untitled',
    'seed': '',
    'center': 0,
    'height': 30,
    'max_hill': 5,
    'ground_height': 10
}


def new_save(meta):

    meta = check_meta(meta)

    # Find unique dir name
    while os.path.isdir(os.path.join('maps', meta['name'])):
        meta['name'] += '-'
    os.mkdir(os.path.join('maps', meta['name']))

    save_meta(meta['name'], meta)


def load_map(save):

    try:
        with open(os.path.join('maps', save, 'meta.json')) as f:
            data = json.load(f)
        meta = check_meta(data)

    except FileNotFoundError:
        meta = default_meta

    try:
        with open(os.path.join('maps', save, 'map.blk')) as f:
            data = f.readlines()
        map_ = check_map(data, meta)

    except FileNotFoundError:
        map_ = {}

    save_map(save, map_)
    save_meta(save, meta)

    return meta, map_


def check_meta(meta):

    # Create meta items if needed
    for key, default in default_meta.items():
        try:
            meta[key]
        except KeyError:
            meta[key] = default

    return meta


def check_map(data, meta):

    map_ = {}

    for line in data:
        # Parses map file
        key, slice_ = line.split('<sep>')
        slice_ = list(slice_)

        # Removes new line char if it exists
        map_[key] = slice_ if not slice_[-1] == '\n' else slice_[:-1]

    for key, slice_ in map_.items():
        if not len(slice_) == meta['height']:

            if len(slice_) < meta['height']:
                # Extend slice height
                slice_ = [' '] * (meta['height'] - len(slice_)) + slice_
            elif len(slice_) > meta['height']:
                # Truncate slice height
                slice_ = slice_[:meta['height']]

            map_[key] = slice_

    return map_


def save_meta(save, meta):

    # Save meta file
    with open(os.path.join('maps', save, 'meta.json'), 'w') as f:
        json.dump(meta, f)


def save_map(save, map_):

    # Save map file
    with open(os.path.join('maps', save, 'map.blk'), 'a') as f:
        for key, slice_ in map_.items():
            f.write(key+'<sep>'+''.join(slice_)+'\n')
