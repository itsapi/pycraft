from colours import *


blocks = {
    ' ': {
        'char': ' ',
        'name': 'Air',
        'colours': {
            'fg': None,
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 0
    },
    '-': {
        'char': '░ᚇ~',
        'name': 'Grass',
        'colours': {
            'fg': rgb(.1, .8, .1),
            'bg': rgb(0, .4, 0),
            'style': None
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 20
    },
    'v': {
        'char': 'v',
        'name': 'Tall Grass',
        'colours': {
            'fg': rgb(.1, .8, .1),
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': True,
        'hierarchy': 0,
        'placed_on': '-v'
    },
    '|': {
        'char': '#',
        'name': 'Wood',
        'colours': {
            'fg': rgb(.45, .26, .12),
            'bg': rgb(0.3, 0.25, 0.15),
            'style': None
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 10
    },
    '@': {
        'char': '@',
        'name': 'Leaves',
        'colours': {
            'fg': GREEN,
            'bg': rgb(0.15, 0.37, 0.09),
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 5
    },
    '#': {
        'char': ' ',
        'name': 'Stone',
        'colours': {
            'fg': None,
            'bg': grey(.15),
            'style': None
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 50
    },
    'x': {
        'char': 'x',
        'name': 'Coal',
        'colours': {
            'fg': rgb(0, 0, 0),
            'bg': grey(.15),
            'style': BOLD
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 55
    },
    '+': {
        'char': '+',
        'name': 'Iron',
        'colours': {
            'fg': rgb(0.8, 0.19, 0.15),
            'bg': grey(.15),
            'style': BOLD
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 60
    },
    ':': {
        'char': ':',
        'name': 'Redstone',
        'colours': {
            'fg': rgb(0.88, 0.06, 0.0),
            'bg': grey(.15),
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 65
    },
    '"': {
        'char': '"',
        'name': 'Gold',
        'colours': {
            'fg': rgb(.8, .4, 0),
            'bg': grey(.15),
            'style': BOLD
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 70
    },
    'o': {
        'char': 'o',
        'name': 'Diamond',
        'colours': {
            'fg': rgb(0.0, 0.41, 0.64),
            'bg': grey(.15),
            'style': BOLD
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 75
    },
    '.': {
        'char': 'o',
        'name': 'Emerald',
        'colours': {
            'fg': rgb(0.02, 0.88, 0.25),
            'bg': grey(.15),
            'style': BOLD
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 80
    },
    '_': {
        'char': '#',
        'name': 'Bedrock',
        'colours': {
            'fg': grey(.3),
            'bg': grey(.15),
            'style': None
        },
        'solid': True,
        'breakable': False,
        'hierarchy': 100
    },
    '/': {
        'char': '/',
        'name': 'Sticks',
        'colours': {
            'fg': rgb(0.3, 0.25, 0.15),
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 10,
        'recipe': {
            '|': 1
        },
        'crafts': 6
    },
    'i': {
        'char': '¡i',
        'name': 'Torch',
        'colours': {
            'fg': YELLOW,
            'bg': None,
            'style': BOLD
        },
        'solid': False,
        'breakable': True,
        'hierarchy': 10,
        'recipe': {
            '/': 1,
            'x': 1
        },
        'crafts': 4,
        'light': 7,
        'placed_on_solid': True
    },
    '=': {
        'char': '=',
        'name': 'Ladder',
        'colours': {
            'fg': rgb(0.3, 0.27, 0.19),
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': True,
        'hierarchy': 10,
        'recipe': {
            '/': 3
        },
        'placed_on': '=',
        'placed_on_solid': True
    },
    '*': {
        'char': '*',
        'name': 'Player head',
        'colours': {
            'fg': WHITE,
            'bg': None,
            'style': BOLD
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1000
    },
    '^': {
        'char': '^',
        'name': 'Player feet',
        'colours': {
            'fg': WHITE,
            'bg': None,
            'style': BOLD
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1000
    },
    'X': {
        'char': 'X',
        'name': 'Cursor',
        'colours': {
            'fg': RED,
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'hierarchy': 1010
    },
    '1': {
        'char': '⚒T',
        'name': 'Wooden Pickaxe',
        'colours': {
            'fg': rgb(0.3, 0.25, 0.15),
            'bg': None,
            'style': DARK
        },
        'solid': False,
        'breakable': False,
        'strength': 50,
        'recipe': {
            '/': 2,
            '|': 3
        }
    },
    '2': {
        'char': '⚒T',
        'name': 'Stone Pickaxe',
        'colours': {
            'fg': DARK_GRAY,
            'bg': None,
            'style': None
        },
        'solid': False,
        'breakable': False,
        'strength': 60,
        'recipe': {
            '/': 2,
            '#': 3
        }
    },
    '3': {
        'char': '⚒T',
        'name': 'Iron Pickaxe',
        'colours': {
            'fg': rgb(0.8, 0.19, 0.15),
            'bg': None,
            'style': BOLD
        },
        'solid': False,
        'breakable': False,
        'strength': 75,
        'recipe': {
            '/': 2,
            '+': 3
        }
    },
    '4': {
        'char': '⚒T',
        'name': 'Diamond Pickaxe',
        'colours': {
            'fg': rgb(0.0, 0.41, 0.64),
            'bg': None,
            'style': BOLD
        },
        'solid': False,
        'breakable': False,
        'strength': 80,
        'recipe': {
            '/': 2,
            'o': 3
        }
    }
}

world_gen = {
    'height': 30,
    'max_hill': 15,
    'min_grad': 5,
    'ground_height': 10,
    'chunk_size': 16,
    'max_biome_size': 50,
    'biome_tree_weights': [0]*2 + [.05]*2 + [.2],
    'tall_grass_rate': .25,
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
         (1, 1, 0, 0, 1, 1, 0)),
        ((0, 0, 0, 0, 1),
         (0, 0, 1, 1, 0),
         (0, 1, 0, 0, 0),
         (0, 1, 0, 0, 0),
         (1, 1, 0, 0, 0),
         (1, 0, 0, 0, 0),
         (1, 1, 0, 0, 0),
         (0, 1, 0, 0, 0),
         (0, 1, 0, 1, 1),
         (0, 0, 1, 0, 0)),
        ((0, 0, 1),
         (1, 0, 0),
         (0, 1, 0)),
        ((0, 0, 0, 1, 0, 1),
         (0, 1, 1, 1, 1, 0),
         (1, 1, 0, 0, 0, 0),
         (0, 1, 1, 0, 1, 1),
         (0, 0, 1, 1, 0, 1))
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
        ['Cycle inventory down', 'O'],
        ['Cycle inventory up', 'U'],
        ['Toggle crafting menu', 'C'],
        ['Craft selected item', 'I']
    ],
    'Menus:': [
        ['Move up', 'W or UP'],
        ['Move down', 'S or DOWN'],
        ['Select', 'SPACE or RETURN'],
        ['Pause', 'SPACE or RETURN']
    ]
}
