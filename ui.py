import sys
import json

from nbinput import BlockingInput, escape_code, UP, DOWN, RIGHT, LEFT
from console import CLS, REDRAW, WIDTH, HEIGHT, SHOW_CUR, HIDE_CUR
from colors import *

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

    STAR = colorStr('*', YELLOW)
    options = [x for x in options if x is not None]

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not str(char) in ' \n':

            # Print menu
            out = ''
            for i, option in enumerate(options):
                if i == selection:
                    out += STAR + colorStr(option[0], style=BOLD) + STAR
                else:
                    out += ' ' + option[0] + ' '
                out += '\n'
            print(REDRAW + title(name) + out)

            # Wait for useful input
            while True:
                char = str(escape_code(bi))
                if char in ' \n':
                    break
                if char in 'Ww'+UP:
                    selection -= 1
                    break
                if char in 'Ss'+DOWN:
                    selection += 1
                    break
            selection %= len(options)
        print(CLS)
    # Execute function of selection
    return options[selection][1]()


def main():
    """ Loops the main menu until the user loads a save. """

    print(CLS)
    data = None
    while not data:
        data, local = menu('Main menu', (
            ('New Save', new),
            ('Load Save', load),
            ('Delete Save', delete),
            ('Multiplayer', servers),
            ('Help', help_),
            ('Exit', sys.exit)
        ))

    return data, local


def lambda_gen(func, var):
    """ Creates a lambda for to call a function with a parameter. """
    return lambda: func(var)


def title(name):
    """ Returns a padded coloured string containing the title. """
    return ' {title}\n\n'.format(
        title = colorStr('{name}\n {_}'.format(
            name = name,
            _ = ('=' * len(name))
        ), style=BOLD)
    )


def load():
    """ A menu for selecting a save to load. """
    saves_list = saves.list_saves()
    return menu(
        'Load save',
        ([(save[1]['name'], lambda_gen(lambda s: s, save[0]))
          for save in saves_list] + [back])
    ), True


def delete():
    """ A menu for selectng a save to delete. """
    saves_list = saves.list_saves()
    return menu(
        'Delete save',
        ([(save[1]['name'], lambda_gen(saves.delete_save, save[0]))
          for save in saves_list] + [back])
    ), None


def new():
    """ Lets the user enter a save name, then it creates and loads the save. """

    print(REDRAW + title('New save'), end='')
    meta = {}
    meta['name'] = input(colorStr(' Save name', style=BOLD)
                         + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR)
    if not meta['name']:
        print(CLS)
        return None, None

    meta['seed'] = input(colorStr(' Map seed', style=BOLD)
                         + ' (leave blank to randomise): ' + SHOW_CUR)
    print(HIDE_CUR)
    save = saves.new_save(meta)
    return save, True


def servers():
    """ A menu for selecting a server to join. """
    server_list = saves.list_servers()
    return menu(
        'Join server',
        ([('{}:{}'.format(*server), lambda_gen(lambda s: s, server))
          for server in server_list] +
          [('Add new server', add_server), back])
    ), False


def add_server():
    """ Get ip and port of server to connect to, then load world from server. """

    print(REDRAW + title('Connect to server'), end='')

    ip = input(colorStr(' Server IP', style=BOLD)
               + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR)
    if not ip:
        print(CLS)
        return None
    port = input(colorStr(' Server port', style=BOLD)
                 + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR)
    if not port:
        print(CLS)
        return None

    saves.add_server(ip, port)

    return ip, port


def pause(server):
    print(CLS)

    port_item = None
    multiplayer_item = None

    if server.server is not None:
        if server.server:
            multiplayer_item = ('Disable Multiplayer', server.kill_server)
            port_item = ('Show Port', lambda: show_port(server.port))
        else:
            multiplayer_item = ('Enable Multiplayer', server.init_server)

    return menu('Paused', (
        ('Resume', lambda: None),
        ('Help', help_),
        multiplayer_item,
        port_item,
        ('Main Menu', lambda: 'exit')
    ))


def show_port(port):
    out = REDRAW + '\n'
    out += 'Port: {}\n\n'.format(port)
    out += 'Back...\n'
    print(out)

    wait_for_input()

    print(CLS)


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
    return None, None


def name(meta):
    print(REDRAW)

    name = None
    while not name:
        name = input('Type your name: ' + SHOW_CUR)
        print(HIDE_CUR + REDRAW)

    print(CLS)

    meta['name'] = name
    saves.save_global_meta(meta)

    return name


def error(message):
    print(CLS + REDRAW + '\n' + colorStr(message, fg=RED) + '\n\nBack...\n')

    wait_for_input()

    print(CLS)


def wait_for_input():
    with BlockingInput() as bi:
        while not str(bi.char()) in ' \n':
            pass
