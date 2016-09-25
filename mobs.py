import random
import player, terrain
from console import log


mob_limit = 100
new_mob_id = 0
mob_rate = 0.1

def update(mobs, players, map_):
    updated_mobs = spawn(mobs, map_)
    removed_mobs = []

    for mob_id, mob in mobs.items():
        mx, my, x_vel = mob['x'], mob['y'], mob['x_vel']
        closest_player = min(players.values(), key=lambda p: abs(p['x'] - mx))

        x_vel += (closest_player['x'] - mx) / 100
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
    return mobs, updated_mobs, removed_mobs


def spawn(mobs, map_):
    global new_mob_id
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
                spot_found = (not terrain.is_solid(map_[mx][my]) and
                              not terrain.is_solid(map_[mx][my - 1]) and
                              terrain.is_solid(map_[mx][my + 1]))
                attempts += 1

            new_mobs[new_mob_id] = {
                'x': mx,
                'y': my,
                'x_vel': 0,
                'type': 'mob'
            }
            new_mob_id += 1

    return new_mobs