from colours import *
from console import supported_chars


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
            'fg': (.1, .8, .1),
            'bg': (0, .4, 0),
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
            'fg': (.1, .8, .1),
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
            'fg': (.45, .26, .12),
            'bg': (0.3, 0.25, 0.15),
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
            'fg': (0, .5, 0),
            'bg': (0.15, 0.37, 0.09),
            'style': DARK
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 5
    },
    '#': {
        'char': '~',
        'name': 'Stone',
        'colours': {
            'fg': (.15, .15, .15),
            'bg': (.15, .15, .15),
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
            'fg': (0, 0, 0),
            'bg': (.15, .15, .15),
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
            'fg': (0.8, 0.19, 0.15),
            'bg': (.15, .15, .15),
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
            'fg': (0.88, 0.06, 0.0),
            'bg': (.15, .15, .15),
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
            'fg': (.8, .4, 0),
            'bg': (.15, .15, .15),
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
            'fg': (0.0, 0.41, 0.64),
            'bg': (.15, .15, .15),
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
            'fg': (0.02, 0.88, 0.25),
            'bg': (.15, .15, .15),
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
            'fg': DARK_GRAY,
            'bg': (.15, .15, .15),
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
            'fg': (0.3, 0.25, 0.15),
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
        'char_left': '/',
        'char_right': '\\',
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
        'light_radius': 7,
        'light_colour': (.2,.8,.8),
        'placed_on_solid': True,
        'placed_on_wall': True
    },
    '=': {
        'char': '=',
        'name': 'Ladder',
        'colours': {
            'fg': (0.3, 0.27, 0.19),
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
    '?': {
        'char': '?',
        'name': 'TNT',
        'colours': {
            'fg': RED,
            'bg': None,
            'style': None
        },
        'solid': True,
        'breakable': True,
        'hierarchy': 85,
        'recipe': {
            '|': 2,
            ':': 1,
            'x': 6
        }
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
            'fg': (0.3, 0.25, 0.15),
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
            'fg': (.15, .15, .15),
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
            'fg': (0.8, 0.19, 0.15),
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
            'fg': (0.0, 0.41, 0.64),
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
    'height': 200,
    'max_hill': 15,
    'min_grad': 5,
    'ground_height': 150,
    'chunk_size': 16,
    'min_biome': 16,
    'max_biome': 64,
    'max_cave_radius': 10,
    'cave_chance': 0.1,
    'biomes': {
        'plains': {
            'chance': .3,
            'trees': 0,
            'grass': .15
        },
        'normal': {
            'chance': .3,
            'trees': .05,
            'grass': .1
        },
        'forest': {
            'chance': .3,
            'trees': .2,
            'grass': 0
        }
    },

    'day_colour': (0,.4,1),
    'night_colour': (0,0,.2),
    'sun_light_radius': 25,
    'moon_light_radius': 10,
    'sun_colour': (.8,.6,0),
    'moon_colour': (1,1,1),
    'sun_light_colour': (0,1,1),
    'moon_light_colour': (.6,.6,.8),

    # TODO: Densities need tuning.
    'ores': {
        'coal': {
            'char': 'x',
            'vain_size': 4,
            'vain_density': .4,
            'chance': 0.5,
            'upper': 1,
            'lower': 0
        },
        'iron': {
            'char': '+',
            'vain_size': 3,
            'vain_density': .3,
            'chance': 0.1,
            'upper': 1/2,
            'lower': 0
        },
        'redstone': {
            'char': ':',
            'vain_size': 4,
            'vain_density': .6,
            'chance': 0.03,
            'upper': 1/5,
            'lower': 0
        },
        'gold': {
            'char': '"',
            'vain_size': 2,
            'vain_density': .3,
            'chance': 0.02,
            'upper': 1/3,
            'lower': 0
        },
        'diamond': {
            'char': 'o',
            'vain_size': 2,
            'vain_density': .5,
            'chance': 0.01,
            'upper': 1/6,
            'lower': 0
        },
        'emerald': {
            'char': '.',
            'vain_size': 1,
            'vain_density': 1,
            'chance': 0.002,
            'upper': 1/5,
            'lower': 0
        }
    },
    'trees': (  # TODO: Preprocessing should be done on these, to give the data
                #         the terrain gen needs.
        {
            'chance': 1,
            'leaves': ((0, 1, 1),
                       (1, 1, 0),
                       (0, 1, 1))
        },
        {
            'chance': 1,
            'leaves': ((1, 1, 0, 0, 0, 1, 1),
                       (0, 1, 1, 0, 1, 1, 0),
                       (0, 0, 1, 1, 0, 0, 0),
                       (0, 1, 1, 1, 1, 0, 0),
                       (1, 1, 0, 0, 1, 1, 0))
        },
        {
            'chance': .7,
            'leaves': ((0, 0, 0, 0, 1),
                       (0, 0, 1, 1, 0),
                       (0, 1, 0, 0, 0),
                       (0, 1, 0, 0, 0),
                       (1, 1, 0, 0, 0),
                       (1, 0, 0, 0, 0),
                       (1, 1, 0, 0, 0),
                       (0, 1, 0, 0, 0),
                       (0, 1, 0, 1, 1),
                       (0, 0, 1, 0, 0))
        },
        {
            'chance': 1,
            'leaves': ((0, 0, 1),
                       (1, 0, 0),
                       (0, 1, 0))
        },
        {
            'chance': .9,
            'leaves': ((0, 0, 0, 1, 0, 1),
                       (0, 1, 1, 1, 1, 0),
                       (1, 1, 0, 0, 0, 0),
                       (0, 1, 1, 0, 1, 1),
                       (0, 0, 1, 1, 0, 1))
        },
        {
            'chance': .8,
            'leaves': ((0,0,1,1,0,1,1,0),
                       (0,1,1,1,1,1,1,1),
                       (1,1,1,1,1,1,1,1),
                       (1,1,1,1,1,0,0,0),
                       (1,1,1,1,1,1,1,1),
                       (0,1,1,1,1,1,1,1),
                       (0,0,1,0,1,1,1,0))
        },
        {
        'chance': 1,
        'leaves': ((0, 0, 0, 0, 0, 1, 1, 1, 0),
                   (0, 0, 0, 0, 1, 1, 1, 1, 0),
                   (0, 0, 0, 1, 1, 1, 1, 1, 0),
                   (0, 0, 1, 1, 1, 1, 1, 0, 0),
                   (0, 1, 1, 1, 1, 1, 1, 1, 0),
                   (1, 0, 1, 1, 0, 1, 1, 1, 0),
                   (0, 1, 1, 1, 1, 1, 1, 1, 0),
                   (1, 1, 1, 1, 1, 0, 0, 0, 0),
                   (0, 1, 1, 1, 1, 1, 0, 1, 0),
                   (0, 1, 1, 1, 1, 1, 1, 0, 0),
                   (0, 0, 1, 1, 1, 1, 1, 1, 0),
                   (0, 0, 1, 1, 1, 1, 1, 1, 0),
                   (0, 0, 0, 1, 1, 1, 1, 1, 0),
                   (0, 0, 0, 0, 0, 1, 1, 0, 0),
                   (0, 0, 0, 0, 0, 0, 1, 0, 0))
        }
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


def gen_blocks(blocks):
    for key, block in blocks.items():
        # Get supported version of block char
        blocks[key]['char'] = supported_chars(*block['char'])


gen_blocks(blocks)
