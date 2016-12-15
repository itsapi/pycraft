from player import add_inv

from uuid import uuid4


ttls = {
    'meat': 10
}

items_to_blocks = {
    'meat': '&'
}


def new_item(x, y, type_, t):
    return {
        str(uuid4()): {
            'x': x,
            'y': y,
            'type': type_,
            't0': t,
            'ttl': ttls[type_]
        }
    }


def despawn_items(items, last_tick):
    removed_items = []

    for id_, item in items.items():
        if item['t0'] + item['ttl'] <= last_tick:
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
                add_inv(player['inv'], items_to_blocks[item['type']])

                break

    for id_ in picked_up_items:
        del items[id_]

    return picked_up_items