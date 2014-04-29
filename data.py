from colors import *


clear_bg = lambda char, bg, blocks_: colorStr(
    char,
    bg = blocks_[bg]['colors']['bg'],
    fg = blocks_[char]['colors']['fg'],
    style = blocks_[char]['colors']['style']
)

blocks = {
    ' ': { # Air
        'char': ' ',
        'colors': {
            'fg': None,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 0
    },
    '-': { # Grass
        'char': 'v',
        'colors': {
            'fg': GREEN,
            'bg': GREEN,
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 20
    },
    '|': { # Wood
        'char': '#',
        'colors': {
            'fg': BLACK,
            'bg': MAGENTA,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 10
    },
    '@': { # Leaves
        'char': '@',
        'colors': {
            'fg': GREEN,
            'bg': GREEN,
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 5
    },
    '#': { # Stone
        'char': '~',
        'colors': {
            'fg': None,
            'bg': BLACK,
            'style': CLEAR
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 50
    },
    'x': { # Coal
        'char': 'x',
        'colors': {
            'fg': BLACK,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 55
    },
    '+': { # Iron
        'char': '+',
        'colors': {
            'fg': RED,
            'bg': BLACK,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 60
    },
    ':': { # Redstone
        'char': ':',
        'colors': {
            'fg': RED,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 65
    },
    '"': { # Gold
        'char': '"',
        'colors': {
            'fg': YELLOW,
            'bg': BLACK,
            'style': None
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 70
    },
    'o': { # Diamond
        'char': 'o',
        'colors': {
            'fg': BLUE,
            'bg': BLACK,
            'style': LIGHT
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 75
    },
    '.': { # Emerald
        'char': 'o',
        'colors': {
            'fg': GREEN,
            'bg': BLACK,
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 80
    },
    '_': { # Bedrock
        'char': '#',
        'colors': {
            'fg': BLACK,
            'bg': BLACK,
            'style': LIGHT
        },
        'solid': True,
        'breakable': False,
        'hierarchy': 100
    },
    '*': { # Player head
        'char': '*',
        'colors': {
            'fg': WHITE,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1000
    },
    '^': { # Player feet
        'char': '^',
        'colors': {
            'fg': WHITE,
            'bg': CYAN,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1000
    },
    'X': { # Cursor
        'char': clear_bg,
        'colors': {
            'fg': RED,
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1010
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
            'lower': 1
        },
        'iron': {
            'char': '+',
            'vain_size': 3,
            'chance': 0.03,
            'upper': 15,
            'lower': 1
        },
        'redstone': {
            'char': ':',
            'vain_size': 4,
            'chance': 0.03,
            'upper': 7,
            'lower': 1
        },
        'gold': {
            'char': '"',
            'vain_size': 2,
            'chance': 0.02,
            'upper': 10,
            'lower': 1
        },
        'diamond': {
            'char': 'o',
            'vain_size': 1,
            'chance': 0.01,
            'upper': 5,
            'lower': 1
        },
        'emerald': {
            'char': '.',
            'vain_size': 1,
            'chance': 0.002,
            'upper': 7,
            'lower': 1
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

help_data = {
    'Movement:': [
        ['Move left', 'A'],
        ['Move right', 'D'],
        ['Jump', 'W']
    ],
    'Blocks:': [
        ['Break/place block', 'K'],
        ['Move cursor clockwise', 'L'],
        ['Move cursor anti-clockwise', 'J']
    ],
    'Inventory:': [
        ['Cycle inventory down', ';'],
        ['Cycle inventory up', 'H'],
        ['Drop single item', 'B'],
        ['Drop entire stack', 'CTRL-B']
    ],
    'Menus:': [
        ['Move up', 'W or UP'],
        ['Move down', 'S or DOWN'],
        ['Select', 'SPACE or RETURN'],
        ['Pause', 'SPACE or RETURN']
    ]
}
