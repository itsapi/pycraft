import sys

DEBUG = True


def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
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
    

debug = lambda m: print(repr(m), file=open('log', 'a')) if DEBUG else None

WIDTH, HEIGHT = getTerminalSize()
CLS = '\033[2J'
CLS_END = '\033[0J'
CLS_END_LN = '\033[0K'
REDRAW = '\033[0;0f'
HIDE_CUR = '\033[?25l'
SHOW_CUR = '\033[?25h'
