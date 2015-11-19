import sys
import os


def _get_terminal_size():
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


def debug(*args, trunc=True):
    if DEBUG:
        args = (str(arg)[:100] + '...' if trunc and len(str(arg)) > 100 else arg for arg in args)
        with open(LOG, 'a') as f:
            print(*args, file=f)


def getenv_b(opt):
    """ Converts an enviroment variable into a boolean. """
    o = os.getenv(opt)
    if o:
        return o.lower() in ('true', '1', 'on')


DEBUG = getenv_b('PYCRAFT_DEBUG')
LOG = getenv_b('PYCRAFT_LOG') or 'pycraft.log'

WIDTH, HEIGHT = _get_terminal_size()
CLS = '\033[2J'
CLS_END = '\033[0J'
CLS_END_LN = '\033[0K'
REDRAW = '\033[0;0f'
HIDE_CUR = '\033[?25l'
SHOW_CUR = '\033[?25h'

if DEBUG:
    open(LOG, 'w').close()
