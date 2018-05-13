import mobs, terrain, player


def pathfind_towards_delta(entity, delta, map_):
  updated = False
  kill_entity = False

  ex = entity['x']
  ey = entity['y']
  x_vel = entity['x_vel']

  x_vel += delta / 100
  if abs(x_vel) > 1:
      x_vel = x_vel / abs(x_vel)

  dx = round(x_vel)

  if (ex + dx - 1 not in map_.keys() or
          ex + dx not in map_.keys() or
          ex + dx + 1 not in map_.keys()):
      kill_entity = True

  else:
      dx, dy = player.get_pos_delta(dx, ex, ey, map_)
      ex, ey = ex + dx, ey + dy

      if not terrain.is_solid(map_[ex][ey + 1]):
          ey += 1

      entity['x'] = ex
      entity['y'] = ey
      entity['x_vel'] = x_vel

      updated = True

  return updated, kill_entity