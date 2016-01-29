import sys
import tty
import termios
import os
import time
from fcntl import fcntl, F_GETFL, F_SETFL


UP, DOWN, RIGHT, LEFT = '\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D'


def make_nonblocking(fd):
    return fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | os.O_NONBLOCK)


class NonBlockingInput:

    def __enter__(self):
        make_nonblocking(sys.stdin)
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type_, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

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
