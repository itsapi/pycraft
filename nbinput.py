import sys
import tty
import termios
import os
import time
from fcntl import fcntl, F_GETFL, F_SETFL


keys = {
    '\x1b[A': 'up',
    '\x1b[B': 'down',
    '\x1b[C': 'right',
    '\x1b[D': 'left',
    '\x1b': 'esc',
    '\n': 'enter',
    '\x1b[5~': 'pageup',
    '\x1b[6~': 'pagedown',
    '\x1b[1~': 'home',
    '\x1bOH': 'home',
    '\x1b[2~': 'insert',
    '\x1b[3~': 'delete',
    '\x1b[4~': 'end',
    '\x1bOF': 'end',
}


stdin_blocking_state = True


def make_nonblocking():
    stdin_blocking_state = False
    fcntl(sys.stdin, F_SETFL, fcntl(sys.stdin, F_GETFL) | os.O_NONBLOCK)


def make_blocking():
    stdin_blocking_state = True
    fcntl(sys.stdin, F_SETFL)


class NonBlockingInput:

    def __enter__(self):
        make_nonblocking()
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type_, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        make_blocking()

    def char(self):
        buff = ''
        c = sys.stdin.read(1)
        while c != '':
            buff += c
            c = sys.stdin.read(1)

        if buff == '':
            buff = None

        buff = keys.get(buff, buff)

        return buff


class BlockingInput(NonBlockingInput):

    def char(self):
        c = ''
        while c == '':
            c = sys.stdin.read(1)
            time.sleep(.01)

        buff = ''
        while c != '':
            buff += c
            c = sys.stdin.read(1)

        buff = keys.get(buff, buff)

        return buff


def input_line(prompt):
    prev_stdin_blocking_state = stdin_blocking_state
    make_blocking()

    print(prompt, end='')
    i = input()

    if not prev_stdin_blocking_state:
        make_nonblocking()

    return i


def main():
    try:
        with BlockingInput() as bi:
            while True:
                inp = bi.char()

                # if inp:
                print(repr(inp))

                if inp in ['esc']:
                    break

                time.sleep(.001)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
