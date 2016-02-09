import sys
import re


def _has_colours(stream):
    return hasattr(stream, 'isatty') and stream.isatty()


(TERM_BLACK,
 TERM_RED,
 TERM_GREEN,
 TERM_YELLOW,
 TERM_BLUE,
 TERM_MAGENTA,
 TERM_CYAN,
 TERM_GRAY,
 TERM_DARK_GRAY,
 TERM_LIGHT_RED,
 TERM_LIGHT_GREEN,
 TERM_LIGHT_YELLOW,
 TERM_LIGHT_BLUE,
 TERM_LIGHT_MAGENTA,
 TERM_LIGTH_CYAN,
 TERM_WHITE) = range(16)

BLACK         = (0,   0,   0)
RED           = (2/3, 0,   0)
GREEN         = (0,   2/3, 0)
YELLOW        = (2/3, 1/3, 0)
BLUE          = (0,   0,   2/3)
MAGENTA       = (2/3, 0,   2/3)
CYAN          = (0,   2/3, 2/3)
GRAY          = (2/3, 2/3, 2/3)
DARK_GRAY     = (1/3, 1/3, 1/3)
LIGHT_RED     = (1,   1/3, 1/3)
LIGHT_GREEN   = (1/3, 1,   1/3)
LIGHT_YELLOW  = (1,   1,   1/3)
LIGHT_BLUE    = (1/3, 1/3, 1)
LIGHT_MAGENTA = (1,   1/3, 1)
LIGHT_CYAN    = (1/3, 1,   1)
WHITE         = (1,   1,   1)

NORMAL, BOLD, DARK, ITALICS, UNDERLINE, \
    _, _, INVERT, CLEAR, STRIKETHROUGH = range(10)

_has_colours = _has_colours(sys.stdout)
ansi_escape = re.compile(r'\x1b[^m]*m')


def colour_str(text, settings, fg=None, bg=None, style=None):
    if _has_colours and settings.get('colours', True):
        out = _colour_str(text, fg, bg, style)
    else:
        out = text

    return out


def _colour_str(text, fg=None, bg=None, style=None):
    code = ''

    if bg is not None: code += '\x1b[48;5;{}m'.format(bg)
    if fg is not None: code += '\x1b[38;5;{}m'.format(fg)
    if style is not None: code += '\x1b[{}m'.format(style)

    return code + text + '\x1b[0m'


def rgb(r, g, b):
    if r == g == b:
        rgb = grey(r)

    else:
        rgb = 16 + int(r*5)*36 + int(g*5)*6 + int(b*5)

    return rgb


def round_to_palette(*colour):
    return tuple(int(c*5)/5 for c in colour)


def lightness(colour):
    return 0.2126 * colour[0] + 0.7152 * colour[1] + 0.0722 * colour[2];


def grey(value):
    return 232 + int(value*23)


def bold(t, settings, yes=True):
    return colour_str(t, settings, style=BOLD) if yes else t


def uncolour_str(text):
    return ansi_escape.sub('', text)


if __name__ == '__main__':
    n = 9
    for r in range(n+1):
        for g in range(n+1):
            for b in range(n+1):
                print(colour_str('  ', fg=rgb(r/n, g/n, b/n), bg=rgb((n-r)/n, (n-g)/n, (n-b)/n), style=BOLD), end='')
        print()
