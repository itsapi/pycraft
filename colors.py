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


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(range(8))
NORMAL, BOLD, DARK, ITALICS, UNDERLINE,\
    _, _, INVERT, CLEAR, STRIKETHROUGH = list(range(10))
LIGHT = 'light'
_has_colors = _has_colors(sys.stdout)


def colorStr(text, fg=None, bg=None, style=None):
    if _has_colors:
        if style == LIGHT:
            fg += 60
            style = None

        seq = '\x1b['
        seq += str(0 if bg is None else (bg + 40)) + ';'
        seq += (str(style) + ';') if style is not None else ''
        seq += str((WHITE if fg is None else fg) + 30)
        seq += 'm{}\x1b[0m'.format(text)
        return seq
    else:
        return text


if __name__ == '__main__':
    for style in range(10):
        print(colorStr('hello world', fg=RED, style=style))
