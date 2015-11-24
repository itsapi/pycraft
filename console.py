import sys
import os


def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            pass

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

    if not cr:
        try:
            with open(os.ctermid()) as fd:
                cr = ioctl_GWINSZ(fd)
        except:
            cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

    return int(cr[1]), int(cr[0])


def supported_chars(*tests):
    """
        Takes any number of strings, and returns the first one
            the terminal encoding supports. If none are supported
            it returns '?' the length of the first string.
    """
    for test in tests:
        try:
            test.encode(sys.stdout.encoding)
            return test
        except UnicodeEncodeError:
            pass
    return '?' * len(tests[0])


def debug (*args):
    if DEBUG:
        with open(LOG, 'a') as f:
            print(*args, file=f)


def in_game_debug(string, x, y):
    if IN_GAME_DEBUG:
        print(POS_STR(x, y, string))


LOG = 'pycraft.log'
DEBUG = os.getenv('PYCRAFT_DEBUG')
IN_GAME_DEBUG = os.getenv('PYCRAFT_IN_GAME_DEBUG')
WIDTH, HEIGHT = getTerminalSize()
CLS = '\033[2J'
CLS_END = '\033[0J'
CLS_END_LN = '\033[0K'
REDRAW = '\033[0;0f'
HIDE_CUR = '\033[?25l'
SHOW_CUR = '\033[?25h'
POS_STR = lambda x, y, s: '\033[{};{}H{}'.format(y+1, x+1, s)


open(LOG, 'w').close()
