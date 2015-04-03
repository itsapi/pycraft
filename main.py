from time import time
from math import radians

from console import CLS, SHOW_CUR, HIDE_CUR
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render, server


def main():
    print(HIDE_CUR)
    print(CLS)

    saves.check_map_dir()
    blocks = server.blocks

    # Menu loop
    try:
        while True:
            save = ui.main()
            game(blocks, server.Server(save))

    finally:
        print(SHOW_CUR)
        print(CLS)


def game(blocks, server):
    x = server.get_meta('player_x')
    y = server.get_meta('player_y')
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
    redraw = True
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
    new_slices = {}
    map_ = {}
    alive = True

    crafting_list, crafting_sel = player.get_crafting(
        server.get_meta('inv'),
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

            slice_list = terrain.detect_edges(map_, extended_edges)
            map_.update(server.load_chunks(slice_list))

            # Moving view
            if not edges == old_edges:
                view = terrain.move_map(map_, edges)
                extended_view = terrain.move_map(map_, extended_edges)
                old_edges = edges
                redraw = True

            # Sun has moved
            sun = render.sun(server.get_meta('tick'), width)
            if not sun == old_sun:
                old_sun = sun
                redraw = True

            # Draw view
            if redraw and time() >= 1/FPS + last_out:
                df = 1
                redraw = False
                last_out = time()

                cursor_colour, can_break = player.cursor_colour(
                    x, y, cursor, map_, blocks, server.get_meta('inv'), inv_sel
                )

                objects = player.assemble_player(
                    int(width / 2), y, cursor, cursor_colour, c_hidden
                )

                if crafting:
                    label = player.label(
                        crafting_list, crafting_sel, blocks)
                else:
                    label = player.label(
                        server.get_meta('inv'), inv_sel, blocks)

                crafting_grid = render.render_grid(
                    player.CRAFT_TITLE, crafting, crafting_list, blocks,
                    terrain.world_gen['height']-1, crafting_sel
                )

                inv_grid = render.render_grid(
                    player.INV_TITLE, not crafting, server.get_meta('inv'), blocks,
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
                    server.get_meta('tick')
                )
            else:
                df = 0

            # Respawn player if dead
            if not alive and df:
                alive = True
                x, y = player.respawn(server.get_meta('spawn'))

            # Player falls when no solid block below it
            if dt and not terrain.is_solid(blocks, map_[str(x)][y+1]):
                if jump > 0:
                    # Countdown till fall
                    jump -= 1
                else:
                    # Fall
                    y += 1
                    redraw = True

            # If no block below, kill player
            try:
                block = map_[str(x)][y+1]
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
                        str(inp), map_, x, y, blocks, jump)
                    y += dy
                    x += dx

                    last_move = time()

                dcraft, dcraftC, dcraftN = False, False, False
                if crafting:
                    # Craft if player pressed craft
                    inv, inv_sel, crafting_list, dcraftC = \
                        player.crafting(str(inp), server.get_meta('inv'), inv_sel,
                            crafting_list, crafting_sel, blocks)

                    # Increment/decrement craft no.
                    crafting_list, dcraftN = \
                        player.craft_num(str(inp), server.get_meta('inv'), crafting_list,
                            crafting_sel, blocks)

                    dcraft = dcraftC or dcraftN
                else:
                    # Don't allow breaking/placing blocks if in crafting menu
                    new_slices, inv, inv_sel, dinv = \
                        player.cursor_func(
                            str(inp), map_, x, y, cursor,
                            can_break, inv_sel, server.get_meta('inv'), blocks
                        )

                server.set_meta('inv', inv)

                map_.update(new_slices)

                # Update crafting list
                if dinv or dcraft:
                    crafting_list, crafting_sel = \
                        player.get_crafting(server.get_meta('inv'), crafting_list,
                                            crafting_sel, blocks, dcraftC)

                dc = player.move_cursor(inp)
                cursor = (cursor + dc) % 6

                ds = player.move_sel(inp)
                if crafting:
                    crafting_sel = ((crafting_sel + ds) % len(crafting_list)
                                       if len(crafting_list) else 0)
                else:
                    inv_sel = ((inv_sel + ds) % len(server.get_meta('inv'))
                                  if len(server.get_meta('inv')) else 0)

                if dx or dy or dc or ds or dinv or dcraft:
                    server.set_meta('player_x', x)
                    server.set_meta('player_y', y)
                    saves.save_meta(server.save, server.get_meta())
                    redraw = True
                if dx or dy:
                    c_hidden = True
                if dc:
                    c_hidden = False

                last_inp = time()
                inp = None

            if char in 'c':
                redraw = True
                crafting = not crafting

            # Pause game
            if char in ' \n':
                server.set_meta('player_x', x)
                server.set_meta('player_y', y)
                saves.save_meta(server.save, server.get_meta())
                redraw = True
                if ui.pause() == 'exit':
                    game = False

            dt = server.tick()


if __name__ == '__main__':
    main()
