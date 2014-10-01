import json
import os


def main():
    saves = os.listdir('saves')
    print('Choose a save to convert:\n')
    print('\n'.join('({}) {}'.format(i, save) for i, save in enumerate(saves)))
    save = saves[int(input('> '))]

    # Extract map data from chunk files
    map_ = []
    chunks = (file_ for file_ in os.listdir('saves/' + save)
              if file_.endswith('.chunk'))
    for chunk in chunks:
        with open('saves/{}/{}'.format(save, chunk)) as f:
            data = f.readlines()
        map_ += data

    # Convert map data into object
    slices = {}
    for line in map_:
        key, slice_ = line.split('<sep>')
        slice_ = list(slice_)
        slices[key] = slice_ if not slice_[-1] == '\n' else slice_[:-1]
        slices[key] = ''.join(slices[key][::-1])

    # Split map data into chunks
    chunks = {}
    for pos, slice_ in slices.items():
        try:
            chunks[int(pos) // 16].update({pos: slice_})
        except KeyError:
            chunks[int(pos) // 16] = {pos: slice_}

    # Save chunks to file
    try:
        os.mkdir('saves/{}/chunks'.format(save))
    except FileExistsError:
        pass
    for num, chunk in chunks.items():
        with open('saves/{}/chunks/{}.json'.format(save, num), 'w') as f:
            json.dump(chunk, f, indent=4)


if __name__ == '__main__':
    main()
