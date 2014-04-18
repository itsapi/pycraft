import sys

from nbinput import BlockingInput
from console import CLEAR

from saves import list_saves, new_save, load_save, delete_save


back = ['Back...', lambda: None]


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
    save = None
    while not save:
        save = menu('Main menu', (
            ('New Save', new),
            ('Load Save', load),
            ('Delete Save', delete),
            ('Exit', lambda: sys.exit())
        ))
    return save


def lambda_gen(func, var):
    return lambda: func(var)


def load():
    saves = list_saves()
    return menu(
        'Load save',
        ([(save[1]['name'], lambda_gen(load_save, save[0])) for save in saves]
         + [back])
    )


def delete():
    saves = list_saves()
    return menu(
        'Delete save',
        ([(save[1]['name'], lambda_gen(delete_save, save[0])) for save in saves]
         + [back])
    )


def new():
    print(CLEAR + 'New save\n')
    meta = {
        'name': input('Save name: '),
        'seed': input('Map seed: ')
    }
    save = new_save(meta)
    return load_save(save)