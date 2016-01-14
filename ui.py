from nbinput import BlockingInput, escape_code, UP, DOWN, RIGHT, LEFT
from console import CLS, REDRAW, WIDTH, HEIGHT, SHOW_CUR, HIDE_CUR
from colors import *

import saves
from data import help_data


back = ('Back...', lambda: False)


def menu(name, options, selection=0):
    """
        Executes the users selection from the menu, and returns the result.

        Parameters:
        - name: menu title
        - options: a tuple of option name and option function
    """

    STAR = colorStr('*', YELLOW)
    options = [x for x in options if x is not None]

    print_map = {}
    i = 0
    for j, option in enumerate(options):
        if len(option) > 1:
            print_map[i] = j
            i += 1

    padding = 5
    max_height = HEIGHT - padding
    char = None
    with BlockingInput() as bi:
        while not str(char) in ' \n':
            offset = selection - max(
                min(selection, max_height - padding),
                selection + min(0, max_height - len(options))
            )

            # Print menu
            out = ''
            for i, option in enumerate(options[offset:offset+max_height]):
                if option == ():
                    pass
                elif offset + i == print_map.get(selection):
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
            selection %= len(print_map)
            print(CLS, end='')
    # Execute function of selection
    return options[print_map[selection]][1](), selection


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
    selection = 0
    while data is None:
        data, selection = menu(title, generator(), selection)

    if data is False:
        # Stop at next level
        data = None

    return data


def main(meta):
    """ Loops the main menu until the user loads a save. """

    print(CLS, end='')
    return loop_menu('Main menu', lambda: (
        [('Saves', load_save)] +
        [('Multiplayer', lambda: servers(meta))] +
        [('Help', help_)] +
        [('Exit', lambda: False)]
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
    saves_list = saves.list_saves()
    return ([(save[1]['name'], lambda_gen(func, save[0])) for save in saves_list] +
            [() if saves_list else None])


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
    print(HIDE_CUR, end='')
    if not meta['name']:
        print(CLS, end='')
        return None

    meta['seed'] = input(colorStr(' Map seed', style=BOLD)
                         + ' (leave blank to randomise): ' + SHOW_CUR)
    print(HIDE_CUR, end='')
    save = saves.new_save(meta)

    if save is None:
        error('Error creating save')
    else:
        return {'local': True, 'save': save}


def server_list(meta, func):
    servers_list = meta.get('servers', [])
    return ([('{}:{}'.format(*server), lambda_gen(func, server)) for server in servers_list] +
            [() if servers_list else None])


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
    print(HIDE_CUR, end='')
    if not ip:
        print(CLS, end='')
        return None
    port = input(colorStr(' Server port', style=BOLD)
                 + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR, end='')
    if not port:
        print(CLS, end='')
        return None

    saves.add_server(meta, (ip, port))

    return {'local': False,
            'ip': ip,
            'port': port}


def pause(server):
    print(CLS, end='')

    return loop_menu('Paused', lambda: (
        ('Resume', lambda: False),
        ('Help', help_),
        (None if server.serving is None else (
            ('Disable Multiplayer', server.kill_server)
            if server.serving else
            ('Enable Multiplayer', server.init_server))),
        (('  Port: {}'.format(server.port),) if server.serving else None),

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

    print(CLS, end='')
    return None


def name(meta):
    print(REDRAW, end='')

    name = None
    while not name:
        name = input('Type your name: ' + SHOW_CUR)
        print(HIDE_CUR + REDRAW, end='')

    print(CLS, end='')

    meta['name'] = name
    saves.save_global_meta(meta)

    return name


def error(message):
    print(CLS + REDRAW + '\n' + colorStr(message, fg=RED) + '\n\nBack...\n')

    wait_for_input()

    print(CLS, end='')


def wait_for_input():
    with BlockingInput() as bi:
        while not str(bi.char()) in ' \n':
            pass
