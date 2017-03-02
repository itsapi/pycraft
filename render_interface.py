import sys, glob

from console import log
import saves, render


settings_ref = {}


def import_render_c():
    render_c = None

    sys.path += glob.glob('build/lib.*')
    try:
        import render_c
    except ImportError:
        log('Cannot import C renderer: disabling option.', m='warning')
        settings_ref['render_c'] = False

    saves.save_settings(settings_ref)

    return render_c


def setup_render_module(settings):
    global settings_ref
    settings_ref = settings

    global render_c
    render_c = import_render_c()


def create_lighting_buffer(width, height, x, y, map_, slice_heights, bk_objects, sky_colour, day, lights):
    if settings_ref['render_c']:
        return render_c.create_lighting_buffer(width, height, x, y, map_, slice_heights, bk_objects, sky_colour, day, lights, settings_ref)
    else:
        global day_global
        day_global = day

        log('Not implemented: Python create_lighting_buffer function', m='warning')


def render_map(map_, slice_heights, edges, edges_y, objects, bk_objects, sky_colour, day, lights, settings, redraw_all):
    if settings_ref['render_c']:
        return render_c.render_map(map_, slice_heights, edges, edges_y, objects, sky_colour, settings, redraw_all)
    else:
        return render.render_map(map_, slice_heights, edges, edges_y, objects, bk_objects, sky_colour, day, lights, settings, redraw_all)


def get_light_level(*args):
    if settings_ref['render_c']:
        result = render_c.get_world_light_level(*args)
    else:
        result = day_global
        log('Not implemented: Python get_light_level function', m='warning')

    log('{}'.format(result), m='lighting')
    return result