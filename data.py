from colors import *

blocks = {
    ' ': { # Air
        'char': ' ',
        'colors': {
            'fg': None,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False
    },
    '-': { # Grass
        'char': 'v',
        'colors': {
            'fg': GREEN,
            'bg': GREEN,
            'style': DARK
        },
        'solid': True,
        'breakable': True
    },
    '|': { # Wood
        'char': '#',
        'colors': {
            'fg': BLACK,
            'bg': MAGENTA,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True
    },
    '@': { # Leaves
        'char': '@',
        'colors': {
            'fg': GREEN,
            'bg': GREEN,
            'style': DARK
        },
        'solid': True,
        'breakable': True
    },
    '#': { # Stone
        'char': '~',
        'colors': {
            'fg': None,
            'bg': BLACK,
            'style': CLEAR
        },
        'solid': True,
        'breakable': True
    },
    'x': { # Coal
        'char': 'x',
        'colors': {
            'fg': BLACK,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True
    },
    '+': { # Iron
        'char': '+',
        'colors': {
            'fg': RED,
            'bg': BLACK,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True
    },
    ':': { # Redstone
        'char': ':',
        'colors': {
            'fg': RED,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True
    },
    '"': { # Gold
        'char': '"',
        'colors': {
            'fg': YELLOW,
            'bg': BLACK,
            'style': None
        },
        'solid': True,
        'breakable': True
    },
    'o': { # Diamond
        'char': 'o',
        'colors': {
            'fg': BLUE,
            'bg': BLACK,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True
    },
    'o': { # Emerald
        'char': 'o',
        'colors': {
            'fg': GREEN,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True
    },
    '*': { # Player head
        'char': '*',
        'colors': {
            'fg': WHITE,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False
    },
    '^': { # Player feet
        'char': '^',
        'colors': {
            'fg': WHITE,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False
    },
    'X': { # Cursor
        'char': lambda char, blocks_: colorStr(
            'X',
            bg = blocks_[char]['colors']['bg'],
            fg = blocks_['X']['colors']['fg'],
            style = blocks_['X']['colors']['style']
        ),
        'colors': {
            'fg': WHITE,
            'bg': RED,
            'style': None
        },
        'solid': False,
        'breakable': False
    }
}

world_gen = {
    'height': 30,
    'max_hill': 15,
    'ground_height': 10,
    'chunk_size': 16,
    'ores': {
        'coal': {
            'char': 'x',
            'vain_size': 4,
            'chance': 0.05,
            'upper': 30,
            'lower': 0
        },
        'iron': {
            'char': '+',
            'vain_size': 3,
            'chance': 0.03,
            'upper': 15,
            'lower': 0
        },
        'redstone': {
            'char': ':',
            'vain_size': 4,
            'chance': 0.03,
            'upper': 7,
            'lower': 0
        },
        'gold': {
            'char': '"',
            'vain_size': 2,
            'chance': 0.02,
            'upper': 10,
            'lower': 0
        },
        'diamond': {
            'char': 'o',
            'vain_size': 1,
            'chance': 0.01,
            'upper': 5,
            'lower': 0
        },
        'emerald': {
            'char': 'o',
            'vain_size': 1,
            'chance': 0.002,
            'upper': 7,
            'lower': 0
        }
    },
    'trees': (
        ((0, 1, 1),
         (1, 1, 0),
         (0, 1, 1)),
        ((1, 1, 0, 0, 0, 1, 1),
         (0, 1, 1, 0, 1, 1, 0),
         (0, 0, 1, 1, 0, 0, 0),
         (0, 1, 1, 1, 1, 0, 0),
         (1, 1, 0, 0, 1, 1, 0))
    )
}
