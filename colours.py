import sys
import re


def _has_colours(stream):
    return hasattr(stream, 'isatty') and stream.isatty()


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, LIGHT_GRAY, \
    DARK_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_YELLOW, LIGHT_BLUE, \
    LIGHT_MAGENTA, LIGTH_CYAN, WHITE = range(16)

NORMAL, BOLD, DARK, ITALICS, UNDERLINE, \
    _, _, INVERT, CLEAR, STRIKETHROUGH = range(10)

_has_colours = _has_colours(sys.stdout)
ansi_escape = re.compile(r'\x1b[^m]*m')


def init_colours(colours):
    global _has_colours
    _has_colours &= colours

def colour_str(text, fg=None, bg=None, style=None):
    code, end = '', ''

    if _has_colours:
        if bg is not None: code += '\x1b[48;5;{}m'.format(bg)
        if fg is not None: code += '\x1b[38;5;{}m'.format(fg)
        if style is not None: code += '\x1b[{}m'.format(style)
        end = '\x1b[0m'

    return code + text + end


def rgb(r, g, b):
    return 16 + int(r*5)*36 + int(g*5)*6 + int(b*5)


def rgb6(r, g, b):
    return 16 + int(r)*36 + int(g)*6 + int(b)


def grey(value):
    return 232 + int(value*23)


def bold(t, yes=True):
    return colour_str(t, style=BOLD) if yes else t


def uncolour_str(text):
    return ansi_escape.sub('', text)


if __name__ == '__main__':
    for r in range(6):
        for g in range(6):
            for b in range(6):
                print(colour_str('##', fg=rgb(r/5, g/5, b/5), bg=rgb((5-r)/5, (5-g)/5, (5-b)/5), style=BOLD), end='')
        print()
