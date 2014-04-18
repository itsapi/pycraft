from nbinput import BlockingInput

import saves


def menu(options):

    selection = 0
    char = None
    with BlockingInput() as bi:
        while not char == ' ':

            out = ''
            for i, option in enumerate(options.items()):
                star = '*' if i == selection else ' '
                out += star + option[0] + star + '\n'
            print(chr(27) + '[2J' + out)

            while True:
                char = bi.char()
                if char == ' ':
                    break
                if char == '-':
                    selection -= 1
                    break
                if char == '=':
                    selection += 1
                    break
            selection %= len(options)


def main():
    menu({
        'New Map': new,
        'Load Map': load
    })


def load():

    pass


def new():

    pass
