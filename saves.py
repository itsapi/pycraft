import json


default_meta = {
    'name': 'Untitled',
    'seed': '',
    'center': 0,
    'height': 30,
    'max_hill': 5,
    'ground_height': 10
}


def load_map(save):

    meta = check_meta(save)
    map_ = check_map(save, meta)

    save_map(save, map_)
    save_meta(save, meta)

    return meta, map_


def check_meta(save):
    try:
        meta = json.load(open('maps/' + save + '/meta.json'))

        # Create meta items if needed
        for key, default in default_meta.items():
            try:
                meta[key]
            except KeyError:
                meta[key] = default
    
    except FileNotFoundError:
        # Create default meta if needed
        meta = default_meta

    return meta


def check_map(save, meta):
    try:

        with open('maps/' + save + '/map.blk') as f:
            data = f.readlines()

        map_ = {}

        for line in data:
            key, slice_ = line.split('<sep>')
            slice_ = list(slice_)
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

    except FileNotFoundError:
        map_ = {}

    return map_


def save_map(save, map_):
    # Save map file
    with open('maps/' + save + '/map.blk', 'a') as f:
        for key, slice_ in map_.items():
            f.write(key+'<sep>'+''.join(slice_)+'\n')


def save_meta(save, meta):
    # Save meta file
    with open('maps/' + save + '/meta.json', 'w') as f:
        json.dump(meta, f)
