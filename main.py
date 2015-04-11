from time import time
from math import radians

from console import CLS, SHOW_CUR, HIDE_CUR
from nbinput import NonBlockingInput
import saves, ui, terrain, player, render


def main():
    print(HIDE_CUR)
    print(CLS)

    saves.check_map_dir()
    blocks = render.gen_blocks()

    # Menu loop
    try:
        while True:
            g = Game(blocks, *ui.main())
            g.start()

    finally:
        print(SHOW_CUR)
        print(CLS)


class Game:
    def __init__(self, blocks, meta, map_, save):
        self.blocks = blocks
        self.meta = meta
        self.map_ = map_
        self.save = save

        self.x = meta['player_x']
        self.y = meta['player_y']
        self.dx = 0
        self.dy = 0
        self.dt = 0 # Tick
        self.df = 0 # Frame
        self.dc = 0 # Cursor
        self.ds = 0 # Selector
        self.dinv = False # Inventory
        self.dcraft = False # Crafting
        self.width = 40
        self.FPS = 15 # Max
        self.TPS = 10 # Ticks
        self.IPS = 20 # Input
        self.MPS = 15 # Movement
        self.SUN_TICK = radians(1/32)

        self.old_sun = None
        self.old_edges = None
        self.redraw = False
        self.last_out = time()
        self.last_tick = time()
        self.last_inp = time()
        self.last_move = time()
        self.jump = 0
        self.cursor = 0
        self.crafting = False
        self.crafting_sel = 0
        self.crafting_list = []
        self.inv_sel = 0
        self.c_hidden = True
        self.new_slices = {}
        self.alive = True

        self.crafting_list, self.crafting_sel = player.get_crafting(
            self.meta['inv'],
            self.crafting_list,
            self.crafting_sel,
            self.blocks
        )

    def start(self):
        self.game = True
        with NonBlockingInput() as nbi:
            while self.game:
                self.nbi = nbi
                self.game_loop()

    def game_loop(self):
        # Finds display boundaries
        self.edges = (self.x - int(self.width / 2), self.x + int(self.width / 2))
        self.extended_edges = (self.edges[0]-render.max_light, self.edges[1]+render.max_light)

        # Generates new terrain
        self.slice_list = terrain.detect_edges(self.map_, self.extended_edges)
        for pos in self.slice_list:
            self.new_slices[str(pos)] = terrain.gen_slice(pos, self.meta, self.blocks)
            self.map_[str(pos)] = self.new_slices[str(pos)]

        # Save new terrain to file
        if self.new_slices:
            saves.save_map(self.save, self.new_slices)
            self.new_slices = {}
            self.redraw = True

        # Moving view
        if not self.edges == self.old_edges:
            self.view = terrain.move_map(self.map_, self.edges)
            self.extended_view = terrain.move_map(self.map_, self.extended_edges)
            self.old_edges = self.edges
            self.redraw = True

        # Sun has moved
        self.sun = render.sun(self.meta['tick'], self.width)
        if not self.sun == self.old_sun:
            self.old_sun = self.sun
            self.redraw = True

        # Draw view
        if self.redraw and time() >= 1/self.FPS + self.last_out:
            self.frame()
        else:
            self.df = 0

        # Respawn player if dead
        if not self.alive and self.df:
            self.respawn()

        self.fall()

        # Receive input if a key is pressed
        game_inp, inp = self.input_()
        if time() >= (1/self.IPS) + self.last_inp and self.alive and game_inp:
            self.input_frame(game_inp)

        if inp in 'c':
            self.redraw = True
            self.crafting = not self.crafting

        self.pause(inp)
        self.inc_tick()

    def respawn(self):
        self.alive = True
        self.x, self.y = player.respawn(self.meta)

    def fall(self):
        # Player falls when no solid block below it
        if self.dt and not terrain.is_solid(self.blocks,
                               player.standing_on(self.x, self.y, self.map_)):
            if self.jump > 0:
                # Countdown till fall
                self.jump -= 1
            else:
                # Fall
                self.y += 1
                self.redraw = True

        # If no block below, kill player
        try:
            self.block = self.map_[str(self.x)][self.y+1]
        except IndexError:
            self.alive = False

    def frame(self):
        self.df = 1
        self.redraw = False
        self.last_out = time()

        self.cursor_colour, self.can_break = player.cursor_colour(
            self.x, self.y, self.cursor, self.map_, self.blocks, self.meta['inv'], self.inv_sel
        )

        self.objects = player.assemble_player(
            int(self.width / 2), self.y, self.cursor, self.cursor_colour, self.c_hidden
        )

        if self.crafting:
            self.label = player.label(
                self.crafting_list, self.crafting_sel, self.blocks)
        else:
            self.label = player.label(
                self.meta['inv'], self.inv_sel, self.blocks)

        self.crafting_grid = render.render_grid(
            player.CRAFT_TITLE, self.crafting, self.crafting_list, self.blocks,
            terrain.world_gen['height']-1, self.crafting_sel
        )

        self.inv_grid = render.render_grid(
            player.INV_TITLE, not self.crafting, self.meta['inv'], self.blocks,
            terrain.world_gen['height']-1, self.inv_sel
        )

        self.lights = render.get_lights(self.extended_view, self.edges[0], self.blocks)

        render.render_map(
            self.view,
            self.objects,
            [[self.inv_grid, self.crafting_grid],
             [[self.label]]],
            self.blocks,
            self.sun,
            self.lights,
            self.meta['tick']
        )

    def input_(self):
        char = str(self.nbi.char()).lower()
        game_inp = char if char in 'wadkjliuo-=' else None

        return game_inp, char

    def pause(self, inp):
        if inp in ' \n':
            self.meta['player_x'], self.meta['player_y'] = self.x, self.y
            saves.save_meta(self.save, self.meta)
            self.redraw = True
            if ui.pause() == 'exit':
                self.game = False

    def inc_tick(self):
        if time() >= (1/self.TPS) + self.last_tick:
            self.dt = 1
            self.meta['tick'] += self.SUN_TICK
            self.last_tick = time()
        else:
            self.dt = 0

    def input_frame(self, inp):
        if time() >= (1/self.MPS) + self.last_move:
            # Update player position
            self.dx, self.dy, self.jump = player.get_pos_delta(
                str(inp), self.map_, self.x, self.y, self.blocks, self.jump)
            self.y += self.dy
            self.x += self.dx

            self.last_move = time()

        self.dcraft, self.dcraftC, self.dcraftN = False, False, False
        if self.crafting:
            # Craft if player pressed craft
            self.meta['inv'], self.inv_sel, self.crafting_list, self.dcraftC = \
                player.crafting(str(inp), self.meta['inv'], self.inv_sel,
                    self.crafting_list, self.crafting_sel, self.blocks)

            # Increment/decrement craft no.
            self.crafting_list, self.dcraftN = \
                player.craft_num(str(inp), self.meta['inv'], self.crafting_list,
                    self.crafting_sel, self.blocks)

            self.dcraft = self.dcraftC or self.dcraftN
        else:
            # Don't allow breaking/placing blocks if in crafting menu
            self.new_slices, self.meta['inv'], self.inv_sel, self.dinv = \
                player.cursor_func(
                    str(inp), self.map_, self.x, self.y, self.cursor,
                    self.can_break, self.inv_sel, self.meta, self.blocks
                )

        self.map_.update(self.new_slices)

        # Update crafting list
        if self.dinv or self.dcraft:
            self.crafting_list, self.crafting_sel = \
                player.get_crafting(self.meta['inv'], self.crafting_list,
                                    self.crafting_sel, self.blocks, self.dcraftC)

        self.dc = player.move_cursor(inp)
        self.cursor = (self.cursor + self.dc) % 6

        self.ds = player.move_sel(inp)
        if self.crafting:
            self.crafting_sel = ((self.crafting_sel + self.ds) % len(self.crafting_list)
                               if len(self.crafting_list) else 0)
        else:
            self.inv_sel = ((self.inv_sel + self.ds) % len(self.meta['inv'])
                          if len(self.meta['inv']) else 0)

        if any((self.dx, self.dy, self.dc, self.ds, self.dinv, self.dcraft)):
            self.meta['player_x'], self.meta['player_y'] = self.x, self.y
            saves.save_meta(self.save, self.meta)
            self.redraw = True
        if self.dx or self.dy:
            self.c_hidden = True
        if self.dc:
            self.c_hidden = False

        self.last_inp = time()
        inp = None


if __name__ == '__main__':
    main()
