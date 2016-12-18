from player import add_inv

from uuid import uuid4

import data

item_ttl = 10


def new_item(x, y, blocks, t):
    return {
        str(uuid4()): {
            'x': x,
            'y': y,
            'blocks': blocks,
            't0': t
        }
    }


def despawn_items(items, last_tick):
    removed_items = []

    for id_, item in items.items():
        if item['t0'] + item_ttl <= last_tick:
            removed_items.append(id_)

    for id_ in removed_items:
        del items[id_]

    return removed_items


def pickup_items(items, players):
    picked_up_items = []

    for id_, item in items.items():
        ix, iy = item['x'], item['y']

        for player in players.values():
            px, py = player['x'], player['y']

            if ix == px and iy in [py, py-1]:
                picked_up_items.append(id_)

                for block in item['blocks']:
                    add_inv(player['inv'], block['block'], n=block['num'])

                break

    for id_ in picked_up_items:
        del items[id_]

    return picked_up_items


def items_to_render_objects(items, x, offset):
    objects = []

    for item in items.values():
        object_ = data.render_objects['items'].copy()

        object_['x'] = item['x'] - x + offset
        object_['y'] = item['y']

        objects.append(object_)

    return objects