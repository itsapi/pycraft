from random import random

import render, player


def process_events(events, server):
    new_blocks = {}

    for event in events:
        if event['time_remaining'] <= 0:

            new_blocks.update(event['func'](server, *event['args']))

            events.remove(event)
        else:
            event['time_remaining'] -= 1

    return new_blocks


def boom(server, x, y):
    new_blocks = {}

    radius = 5
    blast_strength = 85

    for tx in range(x - radius*2, x + radius*2):
        new_blocks[tx] = {}

        for ty in range(y - radius, y + radius):

            if (render.in_circle(tx, ty, x, y, radius) and tx in server.map_ and ty >= 0 and ty < len(server.map_[tx]) and
                    player.can_strength_break(server.map_[tx][ty], blast_strength)):

                if not render.in_circle(tx, ty, x, y, radius - 1):
                    if random() < .5:
                        new_blocks[tx][ty] = ' '
                else:
                    new_blocks[tx][ty] = ' '

    server.splash_damage(x, y, radius*2, blast_strength/3)

    return new_blocks
