import sys
import json

from nbinput import BlockingInput, UP, DOWN, RIGHT, LEFT
from console import CLS, REDRAW, WIDTH, HEIGHT
from colours import *

import saves
from data import help_data


back = ('Back...', lambda: None)


def menu(name, options):
    """
        Executes the users selection from the menu, and returns the result.

        Parameters:
        - name: menu title
        - options: a tuple of option name and option function
    """

    STAR = colour_str('*', YELLOW)

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not str(char) in ' \n':

            # Print menu
            out = ''
            for i, option in enumerate(options):
                if i == selection:
                    out += STAR + colour_str(option[0], style=BOLD) + STAR
                else:
                    out += ' ' + option[0] + ' '
                out += '\n'
            print(REDRAW + title(name) + out)

            # Wait for useful input
            while True:
                char = str(bi.char())
                if char in [' ', '\n']:
                    break
                if char in ['W', 'w', UP]:
                    selection -= 1
                    break
                if char in ['S', 's', DOWN]:
                    selection += 1
                    break
            selection %= len(options)
        print(CLS)
    # Execute function of selection
    return options[selection][1]()


def main():
    """ Loops the main menu until the user loads a save. """

    save = None
    while not save:
        save = menu('Main menu', (
            ('New Save', new),
            ('Load Save', load),
            ('Delete Save', delete),
            ('Help', help_),
            ('Exit', sys.exit)
        ))

    return save


def lambda_gen(func, var):
    """ Creates a lambda for to call a function with a parameter. """
    return lambda: func(var)


def title(name):
    """ Returns a padded coloured string containing the title. """
    return ' {title}\n\n'.format(
        title = colour_str('{name}\n {_}'.format(
            name = name,
            _ = ('=' * len(name))
        ), style=BOLD)
    )


def load():
    """ A menu for selectng a save to load. """
    saves_list = saves.list_saves()
    return menu(
        'Load save',
        ([(save[1]['name'], lambda_gen(saves.load_save, save[0]))
          for save in saves_list] + [back])
    )


def delete():
    """ A menu for selectng a save to delete. """
    saves_list = saves.list_saves()
    return menu(
        'Delete save',
        ([(save[1]['name'], lambda_gen(saves.delete_save, save[0]))
          for save in saves_list] + [back])
    )


def new():
    """ Lets the user enter a save name, then it creates and loads the save. """

    print(REDRAW + title('New save'), end='')
    meta = {}
    meta['name'] = input(colour_str(' Save name', style=BOLD)
                         + ' (leave blank to cancel): ')
    if not meta['name']:
        print(CLS)
        return None

    meta['seed'] = input(colour_str(' Map seed', style=BOLD)
                         + ' (leave blank to randomise): ')
    save = saves.new_save(meta)

    if save is None:
        error('Error creating save')
    else:
        return saves.load_save(save)


def pause():
    print(CLS)
    return menu('Paused', (
        ('Resume', lambda: None),
        ('Help', help_),
        ('Main Menu', lambda: 'exit')
    ))


def help_():
    """ Displays the help stored in the help_data list. """

    out = REDRAW + title('Help')

    max_len = max(len(item[0]) for section in help_data.values() for item in section)

    for label, section in help_data.items():
        out += label + '\n'
        for name, key in section:
            out += '   {name:{max_len}} - {key}\n'.format(
                name = name, key = key, max_len = max_len
            )
    out += 'Back...\n'
    print(out)

    wait_for_input()

    print(CLS)
    return None


def error(message):
    print(CLS + REDRAW + '\n' + colour_str(message, fg=RED) + '\n\nBack...\n')

    wait_for_input()

    print(CLS, end='')


def wait_for_input():
    with BlockingInput() as bi:
        while not str(bi.char()) in ' \n':
            pass
