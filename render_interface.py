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


def render_map(*args):
    if settings_ref['render_c']:
        return render_c.render_map(*args)
    else:
        return render.render_map(*args)


def get_light_level(*args):
    result = 1

    if settings_ref['render_c']:
        result = render_c.get_light_level(*args)
    else:
        log('Not implemented: Python get_light_level function', m='warning')

    log('{}'.format(result), m='lighting')
    return result