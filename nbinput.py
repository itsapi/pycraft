import sys
import tty
import termios
import os
import time
from fcntl import fcntl, F_GETFL, F_SETFL


UP, DOWN, RIGHT, LEFT = '\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D'
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
    with BlockingInput() as bi:
        while True:
            c = bi.char()
            if c == chr(27):
                break
            if c:
                print(c)


if __name__ == '__main__':
    main()
