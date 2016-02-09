from nbinput import BlockingInput, UP, DOWN, RIGHT, LEFT
from console import CLS, REDRAW, WIDTH, HEIGHT, SHOW_CUR, HIDE_CUR
from colours import *

import saves
from data import help_data


back = ('Back...', lambda settings: False)


def menu(name, options, settings, selection=0):
    """
        Executes the users selection from the menu, and returns the result.

        Parameters:
        - name: menu title
        - options: a tuple of option name and option function
    """

    STAR = colour_str('*', settings, TERM_YELLOW)
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
            selection %= len(print_map)
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
                    out += STAR + colour_str(option[0], settings, style=BOLD) + STAR
                else:
                    out += ' ' + option[0] + ' '
                out += '\n'
            print(REDRAW + title(name, settings) + out)

            # Wait for useful input
            while True:
                char = str(bi.escape_code())
                if char in ' \n':
                    break
                if char in 'Ww'+UP:
                    selection -= 1
                    break
                if char in 'Ss'+DOWN:
                    selection += 1
                    break
            print(CLS, end='')
    # Execute function of selection
    return options[print_map[selection]][1](settings), selection


def loop_menu(title, generator, settings):
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
        data, selection = menu(title, generator(), settings, selection)

    if data is False:
        # Stop at next level
        data = None

    return data


def main(meta, settings):
    """ Loops the main menu until the user loads a save. """

    print(CLS, end='')
    return loop_menu('Main menu', lambda: (
        [('Saves', load_save)] +
        [('Multiplayer', lambda settings: servers(meta, settings))] +
        [('Settings', edit_settings)] +
        [('Help', help_)] +
        [('Exit', lambda settings: False)]
    ), settings)


def lambda_gen(func, *args, **kwargs):
    """ Creates a lambda to call a function. """
    return lambda settings: func(settings, *args, **kwargs)


def title(name, settings):
    """ Returns a padded coloured string containing the title. """
    return ' {title}\n\n'.format(
        title = colour_str('{name}\n {_}'.format(
            name = name,
            _ = ('=' * len(name))
        ), settings, style=BOLD)
    )


def saves_list(func):
    saves_list = saves.list_saves()
    return ([(save[1]['name'], lambda_gen(func, save[0])) for save in saves_list] +
            [() if saves_list else None])


def load_save(settings):
    """ A menu for selecting a save to load. """

    return loop_menu('Load save', lambda: (
        saves_list(lambda settings, save: {'local': True,
                                           'save': save}) +
        [('Add new save', add_save)] +
        [('Rename save', rename_save)] +
        [('Delete save', delete_save)] +
        [back]),
        settings
    )


def delete_save(settings):
    """ A menu for selecting a save to delete. """
    loop_menu('Delete Save', lambda: (
        saves_list(saves.delete_save) +
        [back]),
        settings
    )
    return None


def rename_save(settings):
    """ A menu for selecting a save to rename. """
    save = loop_menu('Rename Save', lambda: (
        saves_list(lambda s: s) +
        [back]),
        settings
    )

    if not save:
        return None

    print(REDRAW + title('Rename save', settings), end='')
    meta = saves.get_meta(save)
    meta['name'] = input(colour_str(' Save name', settings, style=BOLD)
                         + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR + CLS, end='')

    if meta['name']:
        saves.save_meta(save, meta)


def add_save(settings):
    """ Lets the user enter a save name, then it creates and loads the save. """

    print(REDRAW + title('New save', settings), end='')
    meta = {}
    meta['name'] = input(colour_str(' Save name', settings, style=BOLD)
                         + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR, end='')
    if not meta['name']:
        print(CLS, end='')
        return None

    seed = input(colour_str(' Map seed', settings, style=BOLD)
                 + ' (leave blank to randomise): ' + SHOW_CUR)
    print(HIDE_CUR, end='')

    if seed:
        meta['seed'] = seed

    save = saves.new_save(meta)

    if save is None:
        error('Error creating save', settings)
    else:
        return {'local': True, 'save': save}


def server_list(meta, func):
    servers_list = meta.get('servers', [])
    return ([('{}:{}'.format(*server), lambda_gen(func, server)) for server in servers_list] +
            [() if servers_list else None])


def servers(meta, settings):
    """ A menu for selecting a server to join. """

    return loop_menu('Join server', lambda: (
        server_list(meta, lambda settings, server: {'local': False,
                                                    'ip': server[0],
                                                    'port': server[1]}) +
        [('Add new server', lambda settings: add_server(meta, settings))] +
        [('Delete server', lambda settings: delete_server(meta, settings))] +
        [back]),
        settings
    )


def title_case(s):
    for t in '-_':
        s = ' '.join(s.split(t))
    return s.title()


def set_setting(settings, setting, value):
    default_value = saves.default_settings.get(setting)

    if isinstance(default_value, bool):
        settings[setting] = not settings[setting]

    else:
        print(REDRAW + title('Edit Setting', settings), end='')

        new = input(colour_str(' ' + title_case(setting), settings, style=BOLD)
                   + ' (leave blank to leave unchanged): ' + SHOW_CUR)
        print(HIDE_CUR, end='')

        if new:
            if isinstance(default_value, int):
                new = int(new)
            elif isinstance(default_value, float):
                new = float(new)

            settings[setting] = new

        print(CLS, end='')

    saves.save_settings(settings)


def edit_settings(settings):
    return loop_menu('Settings', lambda: (
        [('{}: {}'.format(title_case(setting), value),
          lambda_gen(set_setting, setting, value)) for setting, value in settings.items()] +
        [back]),
        settings
    )


def delete_server(meta, settings):
    """ A menu for selecting a server to delete. """
    loop_menu('Delete Server', lambda: (
        server_list(meta, lambda s: saves.delete_server(meta, s)) +
        [back]),
        settings
    )
    return None


def add_server(meta, settings):
    """ Get ip and port of server to connect to, then load world from server. """

    print(REDRAW + title('New server', settings), end='')

    ip = input(colour_str(' Server IP', settings, style=BOLD)
               + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR, end='')
    if not ip:
        print(CLS, end='')
        return None
    port = input(colour_str(' Server port', settings, style=BOLD)
                 + ' (leave blank to cancel): ' + SHOW_CUR)
    print(HIDE_CUR, end='')
    if not port:
        print(CLS, end='')
        return None

    saves.add_server(meta, (ip, port))

    return {'local': False,
            'ip': ip,
            'port': port}


def pause(server, settings):
    print(CLS, end='')

    return loop_menu('Paused', lambda: (
        ('Resume', lambda settings: False),
        ('Settings', edit_settings),
        ('Help', help_),
        (None if server.serving is None else (
            ('Disable Multiplayer', server.kill_server)
            if server.serving else
            ('Enable Multiplayer', server.init_server))),
        (('  Port: {}'.format(server.port),) if server.serving else None),

        ('Main Menu', lambda settings: 'exit')
    ), settings)


def help_(settings):
    """ Displays the help stored in the help_data list. """

    out = REDRAW + title('Help', settings)

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


def error(message, settings):
    print(CLS + REDRAW + '\n' + colour_str(message, settings, fg=TERM_RED) + '\n\nBack...\n')

    wait_for_input()

    print(CLS, end='')


def wait_for_input():
    with BlockingInput() as bi:
        while not str(bi.char()) in ' \n':
            pass
