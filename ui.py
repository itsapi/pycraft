import sys

from nbinput import BlockingInput, escape_code, UP, DOWN, RIGHT, LEFT
from console import CLEAR

import saves


back = ['Back...', lambda: None]


def menu(name, options):

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not char == '\n':

            out = ''
            for i, option in enumerate(options):
                star = '*' if i == selection else ' '
                out += star + option[0] + star + '\n'
            print(CLEAR + name + '\n' + '=' * len(name) + '\n\n' + out)

            while True:
                char = escape_code(bi)
                if char == '\n':
                    break
                if char == UP:
                    selection -= 1
                    break
                if char == DOWN:
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
    saves_list = saves.list_saves()
    return menu(
        'Load save',
        ([(save[1]['name'], lambda_gen(saves.load_save, save[0])) for save in saves_list]
         + [back])
    )


def delete():
    saves_list = saves.list_saves()
    return menu(
        'Delete save',
        ([(save[1]['name'], lambda_gen(saves.delete_save, save[0])) for save in saves_list]
         + [back])
    )


def new():
    print(CLEAR + 'New save\n')
    meta = {
        'name': input('Save name: '),
        'seed': input('Map seed: ')
    }
    save = saves.new_save(meta)
    return saves.load_save(save)


def pause():
    return menu('Paused', (
        ('Resume', lambda: None),
        ('Main Menu', lambda: 'exit')
    ))
