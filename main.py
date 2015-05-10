from time import time
from math import radians

from console import CLS, SHOW_CUR, HIDE_CUR, debug
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render, server


def main():
    print(HIDE_CUR)
    print(CLS)

    debug('Start\n')

    # Menu loop
    try:
        name = ui.name()
        saves.check_map_dir()
        blocks = server.blocks

        while True:
            data, local = ui.main()

            if local:
                # Local Server
                game(blocks, server.Server(data, name))
            else:
                # Remote Server
                game(blocks, server.RemoteServer(name, *data))

    finally:
        print(SHOW_CUR)
        print(CLS)


def game(blocks, server):
    x, y = server.pos
    dx = 0
    dy = 0
    dt = 0 # Tick
    df = 0 # Frame
    dc = 0 # Cursor
    ds = 0 # Selector
    dinv = False # Inventory
    dcraft = False # Crafting
    width = 40
    FPS = 15 # Max
    IPS = 20 # Input
    MPS = 15 # Movement

    old_sun = None
    old_edges = None
    last_out = time()
    last_inp = time()
    last_move = time()
    inp = None
    jump = 0
    cursor = 0
    crafting = False
    crafting_sel = 0
    crafting_list = []
    inv_sel = 0
    c_hidden = True
    new_blocks = {}
    alive = True

    crafting_list, crafting_sel = player.get_crafting(
        server.inv,
        crafting_list,
        crafting_sel,
        blocks
    )

    # Game loop
    game = True
    with NonBlockingInput() as nbi:
        while game:
            # Finds display boundaries
            edges = (x - int(width / 2), x + int(width / 2))
            extended_edges = (edges[0]-render.max_light, edges[1]+render.max_light)

            slice_list = terrain.detect_edges(server.map_, extended_edges)
            if slice_list:
                chunk_list = terrain.get_chunk_list(slice_list)
                server.load_chunks(chunk_list)
                server.unload_chunks(extended_edges)

            # Moving view
            if not edges == old_edges or server.view_change:
                view = terrain.move_map(server.map_, edges)
                extended_view = terrain.move_map(server.map_, extended_edges)
                old_edges = edges
                server.redraw = True

            # Sun has moved
            sun = render.sun(server.tick, width)
            if not sun == old_sun:
                old_sun = sun
                server.redraw = True

            # Draw view
            if server.redraw and time() >= 1/FPS + last_out:
                df = 1
                server.redraw = False
                last_out = time()

                cursor_colour, can_break = player.cursor_colour(
                    x, y, cursor, server.map_, blocks, server.inv, inv_sel
                )

                objects = player.assemble_player(
                    int(width / 2), y, cursor, cursor_colour, c_hidden
                )

                label = (player.label(crafting_list, crafting_sel, blocks)
                        if crafting else
                        player.label(server.inv, inv_sel, blocks))

                crafting_grid = render.render_grid(
                    player.CRAFT_TITLE, crafting, crafting_list, blocks,
                    terrain.world_gen['height']-1, crafting_sel
                )

                inv_grid = render.render_grid(
                    player.INV_TITLE, not crafting, server.inv, blocks,
                    terrain.world_gen['height']-1, inv_sel
                )

                lights = render.get_lights(extended_view, edges[0], blocks)

                render.render_map(
                    view,
                    objects,
                    [[inv_grid, crafting_grid],
                     [[label]]],
                    blocks,
                    sun,
                    lights,
                    server.tick
                )
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                x, y = player.respawn(server.get_meta('spawn'))

            # Player falls when no solid block below it
            if (dt and not terrain.is_solid(blocks, server.map_[str(x)][y+1])
                and server.chunk_loaded(x)):

                if jump > 0:
                    # Countdown till fall
                    jump -= 1
                else:
                    # Fall
                    y += 1
                    server.redraw = True

            # If no block below, kill player
            try:
                block = server.map_[str(x)][y+1]
            except IndexError:
                alive = False

            # Receive input if a key is pressed
            char = str(nbi.char()).lower()
            inp = char if char in 'wadkjliuo-=' else None

            # Input Frame
            if time() >= (1/IPS) + last_inp and alive and inp:

                if time() >= (1/MPS) + last_move:
                    # Update player position
                    dx, dy, jump = player.get_pos_delta(
                        str(inp), server.map_, x, y, blocks, jump)
                    y += dy
                    x += dx

                    last_move = time()

                new_blocks, inv, inv_sel, dinv = \
                    player.cursor_func(
                        str(inp), server.map_, x, y, cursor,
                        can_break, inv_sel, server.inv, blocks
                    )

                if dinv:
                    server.inv = inv

                if new_blocks:
                    server.save_blocks(new_blocks)

                dcraft, dcraftC, dcraftN = False, False, False
                if dinv: crafting = False
                if crafting:
                    # Craft if player pressed craft
                    inv, inv_sel, crafting_list, dcraftC = \
                        player.crafting(str(inp), server.inv, inv_sel,
                            crafting_list, crafting_sel, blocks)
                    if dcraftC:
                        server.inv = inv

                    # Increment/decrement craft no.
                    crafting_list, dcraftN = \
                        player.craft_num(str(inp), server.inv, crafting_list,
                            crafting_sel, blocks)

                    dcraft = dcraftC or dcraftN


                # Update crafting list
                if dinv or dcraft:
                    crafting_list, crafting_sel = \
                        player.get_crafting(server.inv, crafting_list,
                                            crafting_sel, blocks, dcraftC)
                    if not len(crafting_list): crafting = False

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                ds = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + ds) % len(crafting_list)
                                       if len(crafting_list) else 0)
                else:
                    inv_sel = ((inv_sel + ds) % len(server.inv)
                                  if len(server.inv) else 0)

                if any((dx, dy, dc, ds, dinv, dcraft)):
                    server.pos = x, y
                    server.redraw = True
                if dx or dy:
                    c_hidden = True
                if dc:
                    c_hidden = False

                last_inp = time()
                inp = None

            if char in 'c':
                server.redraw = True
                crafting = not crafting and len(crafting_list)

            # Pause game
            if char in ' \n':
                server.pos = x, y
                server.redraw = True
                if ui.pause(server) == 'exit':
                    game = False

            dt = server.dt()


if __name__ == '__main__':
    main()
