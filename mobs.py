import random

from math import sqrt

from console import log

from uuid import uuid4

import player, terrain, items


mob_limit = 100
mob_rate = 0.1

max_mob_health = 10
attack_strength = 3
attack_radius = 4
mob_attack_rate = 1

meat_time_to_live = 10

max_spawn_light_level = 0.2


def update(mobs, players, map_, last_tick, get_light_level):
    updated_players = {}
    updated_mobs = spawn(mobs, map_, get_light_level)
    removed_mobs = []
    new_items = {}

    for mob_id, mob in mobs.items():
        mx, my, x_vel = mob['x'], mob['y'], mob['x_vel']

        if mob['health'] <= 0:
            removed_mobs.append(mob_id)
            new_items.update(items.new_item(mx, my, [{'block': '&', 'num': 1}], last_tick))

        else:

            closest_player = min(players.values(), key=lambda p: abs(p['x'] - mx))

            closest_player_dist = closest_player['x'] - mx

            if abs(closest_player_dist) < attack_radius and \
                    mob['last_attack'] + (1/mob_attack_rate) <= last_tick:
                updated_players.update(calculate_mob_attack(mx, my, attack_radius, attack_strength, players))
                mob['last_attack'] = last_tick

            else:

                x_vel += closest_player_dist / 100
                if abs(x_vel) > 1:
                    x_vel = x_vel / abs(x_vel)

                dx = round(x_vel)

                if (mx + dx - 1 not in map_.keys() or
                        mx + dx not in map_.keys() or
                        mx + dx + 1 not in map_.keys()):
                    removed_mobs.append(mob_id)

                else:
                    dx, dy = player.get_pos_delta(dx, mx, my, map_)
                    mx, my = mx + dx, my + dy

                    if not terrain.is_solid(map_[mx][my + 1]):
                        my += 1

                    mob['x'] = mx
                    mob['y'] = my
                    mob['x_vel'] = x_vel

                    updated_mobs[mob_id] = mob

    for mob_id in removed_mobs:
        mobs.pop(mob_id)

    mobs.update(updated_mobs)

    return updated_players, new_items


def spawn(mobs, map_, get_light_level):
    n_mobs_to_spawn = random.randint(0, 5) if random.random() < mob_rate else 0
    new_mobs = {}

    for i in range(n_mobs_to_spawn):
        if len(mobs) + len(new_mobs) < mob_limit:
            spot_found = False
            max_attempts = 100
            attempts = 0
            while not spot_found and attempts < max_attempts:
                mx = random.choice(list(map_.keys()))
                my = random.randint(0, len(map_[mx]) - 2)
                feet = map_[mx][my]
                head = map_[mx][my - 1]
                floor = map_[mx][my + 1]
                spot_found = (not terrain.is_solid(feet) and
                              not terrain.is_solid(head) and
                              terrain.is_solid(floor) and
                              get_light_level(mx, my) < max_spawn_light_level and
                              get_light_level(mx, my - 1) < max_spawn_light_level)
                attempts += 1

            new_mobs[str(uuid4())] = {
                'x': mx,
                'y': my,
                'x_vel': 0,
                'health': max_mob_health,
                'type': 'mob',
                'last_attack': 0
            }

    return new_mobs


def calculate_attack(entity, ax, ay, radius, strength):
    dist_from_attack_sq = (ax - entity['x'])**2 + (ay - entity['y'])**2
    success = False

    if dist_from_attack_sq <= radius**2:
        dist_from_attack = sqrt(dist_from_attack_sq)

        affected_strength = (1 - (dist_from_attack / radius)) * strength
        log(dist_from_attack, affected_strength, m='mobs')

        entity['health'] -= affected_strength

        success = True
    return success


def calculate_player_attack(name, ax, ay, radius, strength, players, mobs):
    updated_players = {}
    updated_mobs = {}

    for test_name, player in players.items():
        if not name == test_name:
            if calculate_attack(player, ax, ay, radius, strength):
                updated_players[test_name] = player

    for mob_id, mob in mobs.items():
        if calculate_attack(mob, ax, ay, radius, strength):
            updated_mobs[mob_id] = mob

    return updated_players, updated_mobs


def calculate_mob_attack(ax, ay, radius, strength, players):
    updated_players = {}

    for test_name, player in players.items():
        if calculate_attack(player, ax, ay, radius, strength):
            updated_players[test_name] = player

    return updated_players
