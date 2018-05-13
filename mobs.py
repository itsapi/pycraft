import random

from math import sqrt
from uuid import uuid4

from console import log

import player, terrain, items, render_interface, pathfinding


mob_limit = 100
mob_rate = 0.1

max_mob_health = 10
attack_strength = 3
attack_radius = 4
mob_attack_rate = 1

meat_time_to_live = 10

spawn_player_range_min = 5
spawn_player_range = 30
max_spawn_light_level = 0.3


def update(mobs, players, map_, last_tick):
    updated_players = {}
    updated_mobs = {}
    removed_mobs = []
    new_items = {}

    for mob_id, mob in mobs.items():
        mx, my, x_vel = mob['x'], mob['y'], mob['x_vel']

        if mob['health'] <= 0:
            removed_mobs.append(mob_id)
            new_items.update(items.new_item(mx, my, [{'block': '&', 'num': 1}], last_tick))

        else:
            closest_player_dist = min(map(lambda p: abs(p['x'] - mx), players.values()))

            if (abs(closest_player_dist) < attack_radius and
                mob['last_attack'] + (1 / mob_attack_rate) <= last_tick):

                updated_players.update(calculate_mob_attack(mx, my, attack_radius, attack_strength, players))
                mob['last_attack'] = last_tick

            else:
                updated, kill_mob = pathfinding.pathfind_towards_delta(mob, closest_player_dist, map_)
                if updated:
                    updated_mobs[mob_id] = mob
                if kill_mob:
                    removed_mobs.append(mob_id)

    for name, player_ in updated_players.items():
        player_['health'] = max(player_['health'], players[name]['health'] - attack_strength)

    for mob_id in removed_mobs:
        mobs.pop(mob_id)

    mobs.update(updated_mobs)

    return updated_players, new_items


def spawn(mobs, players, map_, x_start_range, y_start_range, x_end_range, y_end_range):
    log("spawning", x_start_range, x_end_range, m='mobs');

    n_mobs_to_spawn = random.randint(0, 5) if random.random() < mob_rate else 0
    new_mobs = {}

    max_attempts = 100 * n_mobs_to_spawn
    attempts = 0

    while (len(mobs) + len(new_mobs) < mob_limit and
           len(new_mobs) < n_mobs_to_spawn and
           attempts < max_attempts):

        attempts += 1

        mx = random.randint(x_start_range, x_end_range-1)
        my = random.randint(y_start_range, y_end_range-1)

        if mx not in map_ or my < 1 or my > len(map_[mx]) - 2: continue

        feet = map_[mx][my]
        head = map_[mx][my - 1]
        floor = map_[mx][my + 1]

        closest_player_dist = min(map(lambda p: abs(p['x'] - mx), players.values()))

        spot_found = (not terrain.is_solid(feet) and
                      not terrain.is_solid(head) and
                      terrain.is_solid(floor) and
                      render_interface.get_light_level(mx, my) < max_spawn_light_level and
                      render_interface.get_light_level(mx, my - 1) < max_spawn_light_level and
                      not closest_player_dist < spawn_player_range_min)

        if spot_found:
            new_mobs[str(uuid4())] = {
                'x': mx,
                'y': my,
                'x_vel': 0,
                'health': max_mob_health,
                'type': 'mob',
                'last_attack': 0
            }

    mobs.update(new_mobs)

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
