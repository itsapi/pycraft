# Pycraft

A console based 2D Minecraft, runs best on Unix with Python 3.3+. Built by [grit96](//github.com/grit96) and [olls](//github.com/olls).

Usage: `python3 main.py`

![Pycraft gameplay image](http://cdn.dvbris.com/pycraft.gif)

## Controls

For the best control, you should set your keyboard repeat time to around 200-300ms.

```
Menus:
   Move up                    - W or UP
   Move down                  - S or DOWN
   Select                     - SPACE or RETURN
   Pause                      - SPACE or RETURN
Blocks:
   Break/place block          - K
   Move cursor clockwise      - L
   Move cursor anti-clockwise - J
Inventory:
   Cycle inventory down       - O
   Cycle inventory up         - U
   Toggle crafting menu       - C
   Craft selected item        - I
Movement:
   Move left                  - A
   Move right                 - D
   Jump                       - W
```

## Crafting

A number of items are only obtainable through crafting them using the crafting system.
Items that you can craft with the items in your inventory will automatically show up in the crafting grid.
Press `C` to toggle your selection between inventory and crafting grid, press `I` to craft the currently selected item.

#### Recipes:

- 6 sticks:
   - 1 wood
- 4 torches:
   - 1 stick
   - 1 coal
- ladder:
   - 3 sticks
- wooden pickaxe:
   - 2 sticks
   - 3 wood
- stone pickaxe:
   - 2 sticks
   - 3 stone
- iron pickaxe:
   - 2 sticks
   - 3 iron
- diamond pickaxe:
   - 2 sticks
   - 3 diamonds

####  Tools:

Certain blocks require you to craft the right tool before being able to mine it.
The tool has to be selected in your inventory to be able to use it.
Each tier of pickaxe allows you to break more blocks than the previous tier.

- fist (i.e. don't need a tool):
   - grass
   - tall grass
   - wood
   - leaves
   - torch
   - ladder
- wooden pickaxe:
   - stone
- stone pickaxe:
   - coal
   - iron
- iron pickaxe:
   - redstone
   - gold
   - diamond
- diamond pickaxe:
   - emerald
