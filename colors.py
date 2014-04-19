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
NORMAL, BOLD, DARK, ITALICS, UNDERLINE, _, _, INVERT, CLEAR, STRIKETHROUGH = list(range(10))
LIGHT = 'light'
_has_colors = _has_colors(sys.stdout)


def colorStr(text, fg=WHITE, bg=-40, style=NORMAL):
    if _has_colors:
        if style == LIGHT:
            fg += 60
            style = NORMAL

        seq = '\x1b[{style};{bg};{fg}m{text}\x1b[0m'.format(
            style = style,
            bg = 40 + bg,
            fg = 30 + fg,
            text = text
        )
        return seq
    else:
        return text

if __name__ == '__main__':
    print(colorStr('hello world', fg=RED, bg=WHITE, style=LIGHT))
    print(colorStr('hello world', fg=RED, bg=WHITE))
    print(colorStr('hello world', fg=RED, bg=WHITE, style=DARK))
