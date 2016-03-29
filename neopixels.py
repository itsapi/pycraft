import _rpi_ws281x as ws


def init(width, height):
    leds = ws.new_ws2811_t()

    channel = ws.ws2811_channel_get(leds, 0)

    ws.ws2811_channel_t_count_set(channel, width * height)
    ws.ws2811_channel_t_gpionum_set(channel, 18)
    ws.ws2811_channel_t_invert_set(channel, 0)
    ws.ws2811_channel_t_brightness_set(channel, 31)

    ws.ws2811_t_freq_set(leds, 800000)
    ws.ws2811_t_dmanum_set(leds, 5)

    resp = ws.ws2811_init(leds)
    if resp != 0:
        raise RuntimeError('ws2811_init failed with code {0}'.format(resp))

    return leds

def set_pixel(leds, width, height, x, y, rgb_colour):
    y = height - y - 1
    if not y % 2:
        x = width - x - 1

    pos = y * width + x
    dead_pixels = [18*36, 22*36-1]
    for d in dead_pixels:
        if pos > d:
            pos -= 1

    r, g, b = rgb_colour

    colour = int(g * 255) << 16 | int(r * 255) << 8 | int(b * 255)

    ws.ws2811_led_set(ws.ws2811_channel_get(leds, 0), pos, colour)

def render(leds):
    resp = ws.ws2811_render(leds)
    if resp != 0:
            raise RuntimeError('ws2811_render failed with code {0}'.format(resp))

def deinit(leds):
    ws.ws2811_fini(leds)
    ws.delete_ws2811_t(leds)
