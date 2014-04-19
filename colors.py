import sys


def _has_colors(stream):
    if not hasattr(stream, 'isatty'):
        return False
    if not stream.isatty():
        return False
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum('colors') > 2
    except:
        return False

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, CLEAR = list(range(9))
_has_colors = _has_colors(sys.stdout)


def colorStr(text, fg=WHITE, bg=CLEAR):
    if _has_colors:
        seq = '\x1b[{bg};{fg}m{text}\x1b[0m'.format(
            bg = 40 + bg,
            fg = 30 + fg,
            text = text
        )
        return seq
    else:
        return text

if __name__ == '__main__':
    print(colorStr('hi', fg=BLUE, bg=YELLOW))
