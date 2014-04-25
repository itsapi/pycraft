import sys

from nbinput import BlockingInput, escape_code, UP, DOWN, RIGHT, LEFT
from console import CLS, WIDTH, HEIGHT
from colors import *

import saves


back = ['Back...', lambda: None]


def menu(name, options):
    print('\n' * HEIGHT)

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not char in ' \n':

            out = ''
            for i, option in enumerate(options):
                if i == selection:
                    star = colorStr('*', YELLOW)
                    out += star + colorStr(option[0], style=BOLD) + star
                else:
                    out += ' ' + option[0]
                out += '\n'

            print(title(name) + out)

            while True:
                char = escape_code(bi)
                if char == '\n':
                    break
                if char in 'Ww'+UP:
                    selection -= 1
                    break
                if char in 'Ss'+DOWN:
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


def title(name):
    return '{cls} {title}\n\n'.format(
        cls = CLS,
        title = colorStr('{name}\n {_}'.format(
            name = name,
            _ = ('=' * len(name))
        ), style=BOLD)
    )


def load():
    saves_list = saves.list_saves()
    return menu(
        'Load save',
        ([(save[1]['name'], lambda_gen(saves.load_save, save[0]))
          for save in saves_list] + [back])
    )


def delete():
    saves_list = saves.list_saves()
    return menu(
        'Delete save',
        ([(save[1]['name'], lambda_gen(saves.delete_save, save[0]))
          for save in saves_list] + [back])
    )


def new():
    print(title('New save'), end='')
    meta = {}
    meta['name'] = input(colorStr(' Save name', style=BOLD)
                         + ' (leave blank to cancel): ')
    if not meta['name']:
        return None
    meta['seed'] = input(colorStr(' Map seed', style=BOLD)
                         + ' (leave blank to randomise): ')
    save = saves.new_save(meta)
    return saves.load_save(save)


def pause():
    return menu('Paused', (
        ('Resume', lambda: None),
        ('Main Menu', lambda: 'exit')
    ))
