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

        seq = '\x1b[{bg}{style};{fg}m{text}\x1b[0m'.format(
            style = (';' + str(style)) if style else '',
            bg = 40 + bg,
            fg = 30 + fg,
            text = text
        )
        return seq
    else:
        return text

if __name__ == '__main__':
    for style in range(10):
        print(colorStr('hello world', fg=GREEN, bg=RED, style=style))
