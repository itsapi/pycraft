import data
import colours


def c_escape(s):
    return s.replace('\\', '\\\\')


def translate():
    out = ''

    switch = """
BlockData *
get_block_data(char block_key)
{
    BlockData *result = 0;
    switch(block_key)
    {
"""

    for key, block in sorted(data.blocks.items()):
        variable_name = '{}_block_data'.format(c_escape(block['name'].lower().replace(' ', '_')))

        out += "static BlockData {} = {{\n".format(variable_name)
        out += "    .character = L'{}',\n".format(c_escape(block['char']))

        if 'char_left' in block:
            out += "    .character_left = L'{}',\n".format(c_escape(block['char_left']))

        if 'char_right' in block:
            out += "    .character_right = L'{}',\n".format(c_escape(block['char_right']))

        if block['colours']['fg'] is not None:
            out += "    .colours.fg = (Colour){{{{{fg[0]}, {fg[1]}, {fg[2]}}}}},\n".format(**block['colours'])
        else:
            out += "    .colours.fg.r = -1,\n"

        if block['colours']['bg'] is not None:
            out += "    .colours.bg = (Colour){{{{{bg[0]}, {bg[1]}, {bg[2]}}}}},\n".format(**block['colours'])
        else:
            out += "    .colours.bg.r = -1,\n"

        if 'style' in block['colours'] and block['colours']['style'] is not None:
            styles = {colours.NORMAL: 'NORMAL', colours.BOLD: 'BOLD', colours.DARK: 'DARK', colours.ITALICS: 'ITALICS', colours.UNDERLINE: 'UNDERLINE', colours.INVERT: 'INVERT', colours.CLEAR: 'CLEAR', colours.STRIKETHROUGH: 'STRIKETHROUGH'}
            out += "    .colours.style = {},\n".format(c_escape(styles.get(block['colours']['style'], -1)))
        else:
            out += "    .colours.style = -1,\n"

        out += "    .solid = {},\n".format(c_escape(str(block['solid']).lower()))
        out += "};\n\n"

        switch += "        case '{}':\n".format(key)
        switch += "            result = &{};\n".format(variable_name)
        switch += "            break;\n"

    switch += """
        }
    return result;
}
"""

    out += switch

    out += "\n\nstatic long world_gen_height = {};".format(data.world_gen['height'])
    out += "\n\nstatic Colour cave_colour = {{{{{}, {}, {}}}}};\n".format(*data.lighting['cave_colour'])

    return out


def main():
    print(translate())


if __name__ == '__main__':
	main()