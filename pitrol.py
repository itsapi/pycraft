import RPi.GPIO as GPIO


UP = 16
DOWN = 18
LEFT = 22
RIGHT = 15
RASPBERRY = 19
PI = 8
NORTH = 13
SOUTH = 7
EAST = 12
WEST = 11
INPUTS = (UP, DOWN, LEFT, RIGHT, RASPBERRY, PI, NORTH, SOUTH, EAST, WEST)

YELLOW = 5
GREEN = 3
LEDS = (YELLOW, GREEN)


def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Setup i/o and events.
    for pin in INPUTS:
        GPIO.setup(pin, GPIO.IN)
        # GPIO.add_event_detect(pin, GPIO.RISING)

    for pin in LEDS:
        GPIO.setup(pin, GPIO.OUT)


def led(pin, state=None):
    """ Toggles led if state not set. """
    if pin not in LEDS:
        return False
    GPIO.output(pin, not GPIO.input(pin) if state is None else state)


def input(pin):
    if pin not in INPUTS:
        return False
    return GPIO.event_detected(pin)


def wasd():
    # Map Pitrol buttons to keys.
    WASD = 'w_adk'+chr(2)+'h;jl'
    return ''.join(WASD[i] for i, pin in enumerate(INPUTS) if GPIO.input(pin))


setup()
