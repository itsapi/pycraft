import json

from nbinput import BlockingInput, escape_code, UP, DOWN, RIGHT, LEFT
from console import CLS, REDRAW, WIDTH, HEIGHT, SHOW_CUR, HIDE_CUR
from colors import *

import saves
from data import help_data


back = ('Back...', lambda: False)


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


def loop_menu(title, generator):
    """
        Parameters:
         - generator: Function which generates the `options` argument
             for menu()
         - top: Is the top level menu. Meaning False stays at current level too

        Return values from option functions have these meanings:
         - None: Stays at current level
         - False, other: Drops a level
    """

    data = None
    while data is None:
        data = menu(title, generator())

    if data is False:
        # Stop at next level
        data = None

    return data


def main(meta):
    """ Loops the main menu until the user loads a save. """

    print(CLS)
    return loop_menu('Main menu', lambda: (
        ('Saves', load_save),
        ('Multiplayer', lambda: servers(meta)),
        ('Help', help_),
        ('Exit', lambda: False)
    ))


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


def saves_list(func):
    return [(save[1]['name'], lambda_gen(func, save[0]))
            for save in saves.list_saves()]


def load_save():
    """ A menu for selecting a save to load. """

    return loop_menu('Load save', lambda: (
        saves_list(lambda s: {'local': True,
                              'save': s}) +
        [('Add new save', add_save)] +
        [('Delete save', delete_save)] +
        [back])
    )


def delete_save():
    """ A menu for selecting a save to delete. """
    loop_menu('Delete Save', lambda: (
        saves_list(saves.delete_save) +
        [back])
    )
    return None


def add_save():
    """ Lets the user enter a save name, then it creates and loads the save. """

    print(REDRAW + title('New save'), end='')
    meta = {}
    meta['name'] = input(colorStr(' Save name', style=BOLD)
                         + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR)
    if not meta['name']:
        print(CLS)
        return None

    meta['seed'] = input(colorStr(' Map seed', style=BOLD)
                         + ' (leave blank to randomise): ' + SHOW_CUR)
    print(HIDE_CUR)
    save = saves.new_save(meta)
    return {'local': True, 'save': save}


def server_list(meta, func):
    return [('{}:{}'.format(*server), lambda_gen(func, server))
            for server in meta.get('servers', [])]


def servers(meta):
    """ A menu for selecting a server to join. """

    return loop_menu('Join server', lambda: (
        server_list(meta, lambda s: {'local': False,
                                     'ip': s[0],
                                     'port': s[1]}) +
        [('Add new server', lambda: add_server(meta))] +
        [('Delete server', lambda: delete_server(meta))] +
        [back])
    )


def delete_server(meta):
    """ A menu for selecting a server to delete. """
    loop_menu('Delete Server', lambda: (
        server_list(meta, lambda s: saves.delete_server(meta, s)) +
        [back])
    )
    return None


def add_server(meta):
    """ Get ip and port of server to connect to, then load world from server. """

    print(REDRAW + title('New server'), end='')

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

    saves.add_server(meta, (ip, port))

    return {'local': False,
            'ip': ip,
            'port': port}


def pause(server):
    print(CLS)

    return loop_menu('Paused', lambda: (
        ('Resume', lambda: False),
        ('Help', help_),
        ((('Disable Multiplayer', server.kill_server)
            if server.server else ('Enable Multiplayer', server.init_server))
            if server.server is not None else None),
        (('Show Port', lambda: show_port(server.port)) if server.server else None),
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
    return None


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
