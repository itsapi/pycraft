static BlockData air_block_data = {
    .character = L' ',
    .colours.fg.r = -1,
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData gold_block_data = {
    .character = L'"',
    .colours.fg = (Colour){{0.8, 0.4, 0}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = BOLD,
    .solid = true,
};

static BlockData stone_block_data = {
    .character = L'~',
    .colours.fg = (Colour){{0.15, 0.15, 0.15}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = -1,
    .solid = true,
};

static BlockData player_head_block_data = {
    .character = L'*',
    .colours.fg = (Colour){{1, 1, 1}},
    .colours.bg.r = -1,
    .colours.style = BOLD,
    .solid = false,
};

static BlockData iron_block_data = {
    .character = L'+',
    .colours.fg = (Colour){{0.8, 0.19, 0.15}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = BOLD,
    .solid = true,
};

static BlockData grass_block_data = {
    .character = L'░',
    .colours.fg = (Colour){{0.1, 0.8, 0.1}},
    .colours.bg = (Colour){{0, 0.4, 0}},
    .colours.style = -1,
    .solid = true,
};

static BlockData emerald_block_data = {
    .character = L'o',
    .colours.fg = (Colour){{0.02, 0.88, 0.25}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = BOLD,
    .solid = true,
};

static BlockData sticks_block_data = {
    .character = L'/',
    .colours.fg = (Colour){{0.3, 0.25, 0.15}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData wooden_pickaxe_block_data = {
    .character = L'⚒',
    .colours.fg = (Colour){{0.3, 0.25, 0.15}},
    .colours.bg.r = -1,
    .colours.style = DARK,
    .solid = false,
};

static BlockData stone_pickaxe_block_data = {
    .character = L'⚒',
    .colours.fg = (Colour){{0.15, 0.15, 0.15}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData iron_pickaxe_block_data = {
    .character = L'⚒',
    .colours.fg = (Colour){{0.8, 0.19, 0.15}},
    .colours.bg.r = -1,
    .colours.style = BOLD,
    .solid = false,
};

static BlockData diamond_pickaxe_block_data = {
    .character = L'⚒',
    .colours.fg = (Colour){{0.0, 0.41, 0.64}},
    .colours.bg.r = -1,
    .colours.style = BOLD,
    .solid = false,
};

static BlockData redstone_block_data = {
    .character = L':',
    .colours.fg = (Colour){{0.88, 0.06, 0.0}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = DARK,
    .solid = true,
};

static BlockData ladder_block_data = {
    .character = L'=',
    .colours.fg = (Colour){{0.3, 0.27, 0.19}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData tnt_block_data = {
    .character = L'?',
    .colours.fg = (Colour){{0.6666666666666666, 0, 0}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = true,
};

static BlockData leaves_block_data = {
    .character = L'@',
    .colours.fg = (Colour){{0, 0.5, 0}},
    .colours.bg = (Colour){{0.15, 0.37, 0.09}},
    .colours.style = DARK,
    .solid = true,
};

static BlockData cursor_block_data = {
    .character = L'X',
    .colours.fg = (Colour){{0.6666666666666666, 0, 0}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData player_feet_block_data = {
    .character = L'^',
    .colours.fg = (Colour){{1, 1, 1}},
    .colours.bg.r = -1,
    .colours.style = BOLD,
    .solid = false,
};

static BlockData bedrock_block_data = {
    .character = L'#',
    .colours.fg = (Colour){{0.3333333333333333, 0.3333333333333333, 0.3333333333333333}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = -1,
    .solid = true,
};

static BlockData torch_block_data = {
    .character = L'¡',
    .character_left = L'/',
    .character_right = L'\\',
    .colours.fg = (Colour){{0.6666666666666666, 0.3333333333333333, 0}},
    .colours.bg.r = -1,
    .colours.style = BOLD,
    .solid = false,
};

static BlockData diamond_block_data = {
    .character = L'o',
    .colours.fg = (Colour){{0.0, 0.41, 0.64}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = BOLD,
    .solid = true,
};

static BlockData tall_grass_block_data = {
    .character = L'v',
    .colours.fg = (Colour){{0.1, 0.8, 0.1}},
    .colours.bg.r = -1,
    .colours.style = -1,
    .solid = false,
};

static BlockData coal_block_data = {
    .character = L'x',
    .colours.fg = (Colour){{0, 0, 0}},
    .colours.bg = (Colour){{0.15, 0.15, 0.15}},
    .colours.style = BOLD,
    .solid = true,
};

static BlockData wood_block_data = {
    .character = L'#',
    .colours.fg = (Colour){{0.45, 0.26, 0.12}},
    .colours.bg = (Colour){{0.3, 0.25, 0.15}},
    .colours.style = -1,
    .solid = true,
};


BlockData *
get_block_data(char block_key)
{
    BlockData *result = 0;
    switch(block_key)
    {
        case ' ':
            result = &air_block_data;
            break;
        case '"':
            result = &gold_block_data;
            break;
        case '#':
            result = &stone_block_data;
            break;
        case '*':
            result = &player_head_block_data;
            break;
        case '+':
            result = &iron_block_data;
            break;
        case '-':
            result = &grass_block_data;
            break;
        case '.':
            result = &emerald_block_data;
            break;
        case '/':
            result = &sticks_block_data;
            break;
        case '1':
            result = &wooden_pickaxe_block_data;
            break;
        case '2':
            result = &stone_pickaxe_block_data;
            break;
        case '3':
            result = &iron_pickaxe_block_data;
            break;
        case '4':
            result = &diamond_pickaxe_block_data;
            break;
        case ':':
            result = &redstone_block_data;
            break;
        case '=':
            result = &ladder_block_data;
            break;
        case '?':
            result = &tnt_block_data;
            break;
        case '@':
            result = &leaves_block_data;
            break;
        case 'X':
            result = &cursor_block_data;
            break;
        case '^':
            result = &player_feet_block_data;
            break;
        case '_':
            result = &bedrock_block_data;
            break;
        case 'i':
            result = &torch_block_data;
            break;
        case 'o':
            result = &diamond_block_data;
            break;
        case 'v':
            result = &tall_grass_block_data;
            break;
        case 'x':
            result = &coal_block_data;
            break;
        case '|':
            result = &wood_block_data;
            break;

        }
    return result;
}


static long world_gen_height = 200;
