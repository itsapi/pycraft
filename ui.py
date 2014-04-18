from nbinput import BlockingInput
from console import CLEAR

from saves import list_saves, new_save, load_map


def menu(name, options):

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not char == ' ':

            out = ''
            for i, option in enumerate(options):
                star = '*' if i == selection else ' '
                out += star + option[0] + star + '\n'
            print(CLEAR + name + '\n' + '=' * len(name) + '\n\n' + out)

            while True:
                char = bi.char()
                if char == ' ':
                    break
                if char == '-':
                    selection -= 1
                    break
                if char == '=':
                    selection += 1
                    break
            selection %= len(options)

    return options[selection][1]()


def main():
    return menu('Main menu', (
        ('New Map', new),
        ('Load Map', load)
    ))


def load():
    saves = list_saves()
    return menu('Load save', [(save[1]['name'], lambda: load_map(save[0])) for save in saves])


def new():
    print(CLEAR + 'New save\n')
    meta = {
        'name': input('Map name: '),
        'seed': input('Map seed: ')
    }
    save = new_save(meta)
    return load_map(save)