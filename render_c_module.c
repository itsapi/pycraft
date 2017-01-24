#include <Python.h>
#include <math.h>
#include <stdarg.h>

#include "render.h"

#include "colours.c"
#include "data.c"


#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wchar.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <signal.h>


PyObject *C_RENDERER_EXCEPTION;

static PrintableChar *last_frame;
static bool resize;
static bool redraw_all;
static long width;
static long height;


#define S_POS_STR_FORMAT L"\033[%ld;%ldH"
#define POS_STR_FORMAT_MAX_LEN (sizeof(S_POS_STR_FORMAT))
static wchar_t *POS_STR_FORMAT = S_POS_STR_FORMAT;

size_t
pos_str(long x, long y, wchar_t *result)
{
    return swprintf(result, POS_STR_FORMAT_MAX_LEN, POS_STR_FORMAT, y+1, x+1);
}


#define debug_colour(c) debug(L"%f, %f, %f\n", (c).r, (c).g, (c).b)
void
debug(wchar_t *str, ...)
{
    static int debug_y = 0;
    static wchar_t debug_buff[128];
    size_t pos = pos_str(0, 50 + debug_y++, debug_buff);
    debug_buff[pos] = L'\0';

    wprintf(debug_buff);
    wprintf(L"\033[0K");

    va_list aptr;
    va_start(aptr, str);
    vwprintf(str, aptr);
    va_end(aptr);
    puts("\033[0K");

    if (debug_y > 20)
        debug_y = 0;
}


wchar_t
PyString_AsChar(PyObject *str)
{
    wchar_t result = 0;
    Py_ssize_t size;
    wchar_t *chars = PyUnicode_AsWideCharString(str, &size);
    if (chars && size > 0)
    {
        result = *chars;
    }
    return result;
}


long
get_long_from_PyDict_or(PyObject *dict, char key[], long default_result)
{
    long result = default_result;

    PyObject *item = PyDict_GetItemString(dict, key);
    if (item != NULL)
    {
         result = PyLong_AsLong(item);
    }

    return result;
}


wchar_t
get_block(long x, long y, PyObject *map)
{
    // TODO: Cache this? (hash map?)
    wchar_t result = 0;

    PyObject *column = PyDict_GetItem(map, PyLong_FromLong(x));
    if (column)
    {
        PyObject *block = NULL;
        if (y < PyList_Size(column))
        {
            block = PyList_GetItem(column, y);
        }

        if (block)
        {
            result = PyString_AsChar(block);
        }
    }

    return result;
}


float
lightness(Colour *rgb)
{
    return 0.2126f * rgb->r + 0.7152f * rgb->g + 0.0722f * rgb->b;
}


float
circle_dist(long test_x, long test_y, long x, long y, long r)
{
    return ( pow(test_x - x, 2.0f) / pow(r    , 2.0f) +
             pow(test_y - y, 2.0f) / pow(r*.5f, 2.0f) );
}


float
lit(long x, long y, long lx, long ly, long l_radius)
{
    return fmin(circle_dist(x, y, lx, ly, l_radius), 1.0f);
}


Colour
PyColour_AsColour(PyObject *py_colour)
{
    Colour rgb;
    rgb.r = -1;

    if (py_colour)
    {
        rgb.r = PyFloat_AsDouble(PyTuple_GetItem(py_colour, 0));
        rgb.g = PyFloat_AsDouble(PyTuple_GetItem(py_colour, 1));
        rgb.b = PyFloat_AsDouble(PyTuple_GetItem(py_colour, 2));
    }
    return rgb;
}


wchar_t
get_char(long x, long y, PyObject *map, BlockData *pixel)
{
    // TODO: Implement a cache in get_block?

    wchar_t left_block_key = get_block(x-1, y, map);
    wchar_t right_block_key = get_block(x+1, y, map);
    wchar_t below_block_key = get_block(x, y+1, map);

    wchar_t character = pixel->character;

    if (below_block_key == 0 || !(get_block_data(below_block_key)->solid))
    {
        if (left_block_key != 0 && (get_block_data(left_block_key)->solid) && pixel->character_left != 0)
        {
            character = pixel->character_left;
        }
        else if (right_block_key != 0 && (get_block_data(right_block_key)->solid) && pixel->character_right != 0)
        {
            character = pixel->character_right;
        }
    }

    return character;
}


bool
printable_char_eq(PrintableChar *a, PrintableChar *b)
{
    return (a->character == b->character &&
            colour_eq(&(a->fg), &(b->fg)) &&
            colour_eq(&(a->bg), &(b->bg)) &&
            a->style == b->style);
}


void
get_obj_pixel(long x, long y, PyObject *objects, wchar_t *obj_key_result, Colour *obj_colour_result)
{
    PyObject *iter = PyObject_GetIter(objects);
    PyObject *object;

    while ((object = PyIter_Next(iter)))
    {
        long ox = PyLong_AsLong(PyDict_GetItemString(object, "x"));
        long oy = PyLong_AsLong(PyDict_GetItemString(object, "y"));

        if (ox == x && oy == y)
        {
            wchar_t c = PyString_AsChar(PyDict_GetItemString(object, "char"));
            Colour rgb = PyColour_AsColour(PyDict_GetItemString(object, "colour"));

            if (rgb.r == -1)
            {
                rgb = get_block_data(c)->colours.fg;
            }

            *obj_key_result = c;
            *obj_colour_result = rgb;
            return;
        }
    }
}


void
apply_block_lightness(Colour *result, float lightness)
{
    /*
       Applies a 0-1 lightness to a block colour
    */
    Colour hsv = rgb_to_hsv(result);
    hsv.v *= lightness;
    *result = hsv_to_rgb(&hsv);
}


void
get_lighting_buffer_pixel(LightingBuffer *lighting_buffer, int x, int y, struct PixelLighting **result)
{
    *result = lighting_buffer->screen + y * width + x;
}


void
create_lit_block(long x, long y, long world_x, long world_y, PyObject *map, wchar_t pixel_f_key,
                 PyObject *objects, LightingBuffer *lighting_buffer, Settings *settings,
                 PrintableChar *result, struct PixelLighting **potential_lighting_pixel)
{
    bool light_bg = false;
    bool light_fg = false;

    // Get block bg colour if it isn't transparent
    BlockData *pixel_f = get_block_data(pixel_f_key);
    if (pixel_f->colours.bg.r >= 0)
    {
        result->bg = pixel_f->colours.bg;
        light_bg = true;
    }

    // Get object fg colour and character if there is an object, otherwise get block fg colour and character
    wchar_t obj_key = 0;
    Colour obj_colour;
    get_obj_pixel(x, world_y, objects, &obj_key, &obj_colour);
    if (obj_key != 0)
    {
        result->character = obj_key;
        result->fg = obj_colour;
        light_fg = false;
    }
    else
    {
        result->character = get_char(world_x, world_y, map, pixel_f);

        if (pixel_f->colours.fg.r >= 0)
        {
            result->fg = pixel_f->colours.fg;
            light_fg = true;
        }
    }

    // Light block fg and bg

    if ((settings->fancy_lights > 0) &&
        (light_bg || light_fg))
    {
        // Caller passes in **potential_lighting_pixel and it might get populated with the pointer (optimisation!)
        get_lighting_buffer_pixel(lighting_buffer, x, y, potential_lighting_pixel);
        struct PixelLighting *lighting_pixel = *potential_lighting_pixel;

        // lighting_pixel->lightness is guaranteed to be set for every pixel this frame by add_daylight_lightness_to_lighting_buffer
        float lightness = lighting_pixel->lightness;
        if (light_bg)
        {
            apply_block_lightness(&result->bg, lightness);
        }
        if (light_fg)
        {
            apply_block_lightness(&result->fg, lightness);
        }
    }

    result->style = pixel_f->colours.style;
}


void
create_pixel(long x, long y, long world_x, long world_y, PyObject *map, wchar_t pixel_f_key,
             PyObject *objects, LightingBuffer *lighting_buffer, bool underground, Colour *sky_colour_rgb,
             Settings *settings, PrintableChar *result)
{
    result->bg.r = -1;
    result->fg.r = -1;
    result->style = -1;
    result->character = ' ';

    struct PixelLighting *lighting_pixel = NULL;

    create_lit_block(x, y, world_x, world_y, map, pixel_f_key, objects, lighting_buffer, settings, result, &lighting_pixel);

    // If the block did not set a background colour, add the sky background.
    if (result->bg.r == -1)
    {
        if (lighting_pixel == NULL)
        {
            // If create_lit_block has not filled in lighting_pixel yet, get it now.
            get_lighting_buffer_pixel(lighting_buffer, x, y, &lighting_pixel);
        }

        // lighting_pixel->background_colour_set_on_frame is only set for lit pixels, set the rest to sky_colour/cave colour.

        if (lighting_pixel->background_colour_set_on_frame == lighting_buffer->current_frame)
        {
            result->bg = lighting_pixel->background_colour;
        }
        else
        {
            if (underground)
            {
                result->bg = cave_colour;
            }
            else
            {
                result->bg = *sky_colour_rgb;
            }
        }
    }
}


bool
is_light_behind_a_solid_block(long lx, long ly, long l_height, long l_width, PyObject *map, long left_edge)
{
    bool result = true;

    long x, y;
    for (x = lx; x < lx+l_width; ++x)
    {
        for (y = ly; y > ly-l_height; --y)
        {
            wchar_t block_key = get_block(left_edge + x, y, map);

            if (block_key == 0 ||
                !get_block_data(block_key)->solid)
            {
                result = false;
                break;
            }
        }
    }

    return result;
}


bool
check_light_z(PyObject *py_light, Light *light, long left_edge, long top_edge, PyObject *map, PyObject *slice_heights)
{
    /*
        Lights with z of:
            -2 are not added to the lighting buffer as they are just graphical lights, like the moon.
            -1 are added to the lighting buffer IF they are above the ground, and not behind a solid block.
            0  are always added to the lighting buffer.
    */

    bool result = false;

    if (light->z == -2)
    {
        result = false;
    }
    else if (light->z == -1)
    {
        long buffer_ly = light->y - top_edge;

        // Check light source is above ground

        float ground_height_world = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(left_edge + light->x)));
        float ground_height_buffer = (world_gen_height - ground_height_world) - top_edge;

        if (buffer_ly < ground_height_buffer)
        {
            // Check light source is not behind a solid block

            long l_width = get_long_from_PyDict_or(py_light, "source_width", 1);
            long l_height = get_long_from_PyDict_or(py_light, "source_height", 1);

            if (!is_light_behind_a_solid_block(light->x, light->y, l_height, l_width, map, left_edge))
            {
                result = true;
            }
        }
    }
    else if (light->z == 0)
    {
        result = true;
    }

    return result;
}


void
add_light_pixel_lightness_to_lighting_buffer(int current_frame, struct PixelLighting *pixel, float light_distance, Light *light)
{
    // TODO: Basic lighting mode: threshold

    // TODO: Figure out whether this would be better before (old version) or after inverting the distance?
    light_distance *= lightness(&light->rgb);

    float this_lightness = 1 - light_distance;
    // this_lightness *= lightness(&light->rgb);

    if (pixel->lightness < this_lightness ||
        pixel->lightness_set_on_frame != current_frame)
    {
        pixel->lightness = this_lightness;
        pixel->lightness_set_on_frame = current_frame;
    }
}


void
add_light_pixel_colour_to_lighting_buffer(int current_frame, Settings *settings, struct PixelLighting *pixel, long x, long y, float light_distance, Light *light, PyObject *map, Colour *sky_colour, long left_edge, long top_edge, long slice_height)
{
    /*
        Adds the colour of the light's pixel for the light's light-radius' to the lighting buffer.
    */

    // Check if the background for this pixel is visible
    bool visible = false;

    // First, if the background for this pixel has already been set this frame, then the check has already passed.
    if (pixel->background_colour_set_on_frame == current_frame)
    {
        visible = true;
    }
    else
    {
        // Check if there is no block or a block without a clear background at this position.
        wchar_t block_key = get_block(left_edge+x, top_edge+y, map);
        if (block_key == 0 ||
            get_block_data(block_key)->colours.bg.r == -1)
        {
            visible = true;
        }
    }

    if (visible)
    {
        bool add_to_buffer = true;

        Colour rgb;
        float pixel_background_colour_lightness;

        // Different lighting calculations for above and below ground
        long world_top_to_ground = world_gen_height - slice_height;
        long ground_height_buffer = world_top_to_ground - top_edge;
        if (y > ground_height_buffer)
        {
            // Underground

            // How light's Z values apply to underground background:
            //   -2 invisible
            //   -1 visible if the source is above ground
            //   0 always visible

            if (light->z == -2)
            {
                add_to_buffer = false;
            }
            else if (light->z == -1)
            {
                if (light->y > world_top_to_ground)
                {
                    // Light source is underground
                    add_to_buffer = false;
                }
            }

            // Does light's Z value allow this pixel to light?
            if (add_to_buffer)
            {
                if (settings->fancy_lights > 0)
                {
                    // Fancy lighting

                    // TODO: Fudge this calculation until it looks like the Python renderer!

                    pixel_background_colour_lightness = 1 - light_distance;

                    rgb.r = (cave_colour.r + pixel_background_colour_lightness) * .5f;
                    rgb.g = (cave_colour.g + pixel_background_colour_lightness) * .5f;
                    rgb.b = (cave_colour.b + pixel_background_colour_lightness) * .5f;
                }
                else
                {
                    // Basic lighting
                    rgb = cave_colour;
                    pixel_background_colour_lightness = 0;
                }
            }

        }
        else
        {
            // Above ground

            if (settings->fancy_lights > 0)
            {
                Colour hsv = lerp_colour(&light->hsv, light_distance, sky_colour);
                rgb = hsv_to_rgb(&hsv);

                pixel_background_colour_lightness = lightness(&rgb);
            }
            else
            {
                rgb = CYAN;
                pixel_background_colour_lightness = lightness(&rgb);
            }
        }

        // Update lighting buffer pixel if it's unset this frame or if it's lightness is less than this lights lightness
        if (add_to_buffer &&
            (pixel->background_colour_lightness < pixel_background_colour_lightness ||
             pixel->background_colour_set_on_frame != current_frame))
        {
            pixel->background_colour = rgb;
            pixel->background_colour_lightness = pixel_background_colour_lightness;
            pixel->background_colour_set_on_frame = current_frame;
        }
    }

}


void
add_bk_objects_pixels_colour_to_lighting_buffer(LightingBuffer *lighting_buffer, PyObject *bk_objects, PyObject *slice_heights, long left_edge, long top_edge)
{
    /*
        Adds the pixels of the background objects (sun and moon).
        - Because the function is only setting ~4 blocks with the current
            usage for bk_objects, this function does not mask around solid
            blocks (create_pixel won't use background pixels it doesn't need
            anyway).
        - We do need to mask ground height so the objects don't show up
            underground.
        - We do not need to check brightness as we are not setting light
            pixels, this is just for the actual pixels of the background
            objects.
    */

    PyObject *iter = PyObject_GetIter(bk_objects);
    PyObject *bk_object;
    while ((bk_object = PyIter_Next(iter)))
    {
        long ox = PyLong_AsLong(PyDict_GetItemString(bk_object, "x"));
        long oy = PyLong_AsLong(PyDict_GetItemString(bk_object, "y"));
        long o_width = PyLong_AsLong(PyDict_GetItemString(bk_object, "width"));
        long o_height = PyLong_AsLong(PyDict_GetItemString(bk_object, "height"));
        Colour o_colour = PyColour_AsColour(PyDict_GetItemString(bk_object, "colour"));

        long buffer_x;
        for (buffer_x = ox; buffer_x < ox + o_width; ++buffer_x)
        {
            if (buffer_x >= 0 && buffer_x < width)
            {
                long world_x = left_edge + buffer_x;

                long ground_height_world = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(world_x)));
                long world_top_to_ground = world_gen_height - ground_height_world;

                long world_y;
                for (world_y = oy; world_y > oy - o_height; --world_y)
                {
                    long buffer_y = world_y - top_edge;

                    if (world_y < world_top_to_ground &&
                        buffer_y >= 0 && buffer_y < height)
                    {
                        struct PixelLighting *pixel;
                        get_lighting_buffer_pixel(lighting_buffer, buffer_x, buffer_y, &pixel);

                        pixel->background_colour = o_colour;
                        pixel->background_colour_set_on_frame = lighting_buffer->current_frame;
                    }
                }
            }
        }
    }
}


void
add_daylight_lightness_to_lighting_buffer(LightingBuffer *lighting_buffer, PyObject *lights, PyObject *slice_heights, float day, long left_edge, long top_edge)
{
    /*
        Fills in all the gaps of the lightness lighting buffer with daylight, also overwrites darker than daylight parts.
    */
    long x, y;
    for (x = 0; x < width; ++x)
    {
        long ground_height_world = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(left_edge+x)));
        long ground_height_buffer = (world_gen_height - ground_height_world) - top_edge;

        for (y = 0; y < height; ++y)
        {
            float lightness;

            if (y < ground_height_buffer)
            {
                // Above ground
                lightness = day;
            }
            else if (y < ground_height_buffer + 3)
            {
                // Surface fade

                int d_ground = y - ground_height_buffer;
                float ground_fade = fmin(1.0f, ((float)d_ground / 3.0f));

                lightness = lerp(day, ground_fade, 0.0f);
            }
            else
            {
                // Underground
                lightness = 0;
            }

            struct PixelLighting *pixel;
            get_lighting_buffer_pixel(lighting_buffer, x, y, &pixel);

            if (pixel->lightness < lightness ||
                pixel->lightness_set_on_frame != lighting_buffer->current_frame)
            {
                pixel->lightness = lightness;
                pixel->lightness_set_on_frame = lighting_buffer->current_frame;
            }

            // TODO: Assert pixel->lightness_set_on_frame == lighting_buffer->current_frame
        }
    }
}


void
create_lighting_buffer(LightingBuffer *lighting_buffer, PyObject *lights, PyObject *bk_objects, PyObject *map, Settings *settings, PyObject *slice_heights, float day, Colour *sky_colour, long left_edge, long top_edge)
{
    /*
        - Store the lightness value for every block, calculated from the max of:
          - Lights (passed in from python)
            - Including sun (not moon), when sun is above ground height and not behind a block
          - Day value, fading to 0 at the ground

        - Also stores the background colour for pixels where the block in the map has a clear bg.
          - The colour of the light at radius `r` from the pixel is calculated with:
              hsv_to_rgb( lerp_colour( rgb_to_hsv(light_colour), r, sky_colour ) )
          - The colour is then selected by taking the max lightness of that colour from all the lights reaching this pixel.
    */

    ++lighting_buffer->current_frame;

    PyObject *iter = PyObject_GetIter(lights);
    PyObject *py_light;
    while ((py_light = PyIter_Next(iter)))
    {
        Light light = {
            .x = PyLong_AsLong(PyDict_GetItemString(py_light, "x")),
            .y = PyLong_AsLong(PyDict_GetItemString(py_light, "y")),
            .z = PyLong_AsLong(PyDict_GetItemString(py_light, "z")),
            .radius = PyLong_AsLong(PyDict_GetItemString(py_light, "radius")),
            .rgb = PyColour_AsColour(PyDict_GetItemString(py_light, "colour"))
        };
        light.hsv = rgb_to_hsv(&light.rgb);

        bool add_this_lights_lightness = check_light_z(py_light, &light, left_edge, top_edge, map, slice_heights);

        long buffer_ly = light.y - top_edge;
        long x, y;
        for (x = light.x - light.radius; x <= light.x + light.radius; ++x)
        {
            long slice_height = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(left_edge+x)));

            for (y = buffer_ly - light.radius; y <= buffer_ly + light.radius; ++y)
            {
                // Is pixel on screen?
                if ((x >= 0 && x < width) &&
                    (y >= 0 && y < height))
                {
                    float light_distance = lit(x, y, light.x, buffer_ly, light.radius);
                    if (light_distance < 1)
                    {
                        struct PixelLighting *lighting_pixel;
                        get_lighting_buffer_pixel(lighting_buffer, x, y, &lighting_pixel);

                        if (add_this_lights_lightness)
                        {
                            add_light_pixel_lightness_to_lighting_buffer(lighting_buffer->current_frame, lighting_pixel, light_distance, &light);
                        }

                        add_light_pixel_colour_to_lighting_buffer(lighting_buffer->current_frame, settings, lighting_pixel, x, y, light_distance, &light, map, sky_colour, left_edge, top_edge, slice_height);
                    }
                }
            }
        }
    }

    add_bk_objects_pixels_colour_to_lighting_buffer(lighting_buffer, bk_objects, slice_heights, left_edge, top_edge);

    add_daylight_lightness_to_lighting_buffer(lighting_buffer, lights, slice_heights, day, left_edge, top_edge);
}


bool
terminal_out(ScreenBuffer *frame, PrintableChar *c, long x, long y, Settings *settings)
{
    size_t frame_pos = y * width + x;
    if (!printable_char_eq(last_frame + frame_pos, c) || resize || redraw_all)
    {
        last_frame[frame_pos] = *c;

        size_t old_cur_pos = frame->cur_pos;
        frame->cur_pos += pos_str(x, y, frame->buffer + frame->cur_pos);
        frame->cur_pos += colour_str(c, frame->buffer + frame->cur_pos, settings);

        if (frame->cur_pos >= frame->size)
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Exceeded frame buffer size in terminal_out!");
            return false;
        }
        if (frame->cur_pos - old_cur_pos >= (COLOUR_CODE_MAX_LEN + POS_STR_FORMAT_MAX_LEN))
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Block string length exceeded allocated space!");
            return false;
        }
    }

    return true;
}


bool
setup_frame(ScreenBuffer *frame, LightingBuffer *lighting_buffer, long new_width, long new_height)
{
    resize = false;
    if (new_width != width)
    {
        resize = true;
        width = new_width;
    }
    if (new_height != height)
    {
        resize = true;
        height = new_height;
    }

    if (resize)
    {
        frame->size = width * height * (POS_STR_FORMAT_MAX_LEN + COLOUR_CODE_MAX_LEN);
        frame->buffer = (wchar_t *)realloc(frame->buffer, frame->size * sizeof(wchar_t));
        if (!frame->buffer)
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Could not allocate frame buffer!");
            return false;
        }

        last_frame = (PrintableChar *)realloc(last_frame, width * height * sizeof(PrintableChar));
        if (!last_frame)
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Could not allocate last frame buffer!");
            return false;
        }

        lighting_buffer->screen = (struct PixelLighting *)realloc(lighting_buffer->screen, width * height * sizeof(struct PixelLighting));
        if (!lighting_buffer->screen)
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Could not allocate lighting map!");
            return false;
        }
    }

    frame->cur_pos = 0;
    return true;
}


static PyObject *
render_map(PyObject *self, PyObject *args)
{
    static ScreenBuffer frame;
    static LightingBuffer lighting_buffer = {.current_frame = 0};

    float day;

    long left_edge,
         right_edge,
         top_edge,
         bottom_edge;

    PyObject *map,
             *slice_heights,
             *objects,
             *bk_objects,
             *py_sky_colour,
             *lights,
             *py_settings;

    if (!PyArg_ParseTuple(args, "OO(ll)(ll)OOOfOOl:render", &map, &slice_heights,
            &left_edge, &right_edge, &top_edge, &bottom_edge, &objects, &bk_objects,
            &py_sky_colour, &day, &lights, &py_settings, &redraw_all))
    {
        PyErr_SetString(C_RENDERER_EXCEPTION, "Could not parse arguments!");
        return NULL;
    }

    Colour sky_colour_hsv = PyColour_AsColour(py_sky_colour);
    Colour sky_colour_rgb = hsv_to_rgb(&sky_colour_hsv);

    Settings settings = {
        .terminal_output = PyLong_AsLong(PyDict_GetItemString(py_settings, "terminal_output")),
        .fancy_lights = PyLong_AsLong(PyDict_GetItemString(py_settings, "fancy_lights")),
        .colours = PyLong_AsLong(PyDict_GetItemString(py_settings, "colours"))
    };

    long cur_width = right_edge - left_edge;
    long cur_height = bottom_edge - top_edge;

    if (!setup_frame(&frame, &lighting_buffer, cur_width, cur_height))
        return NULL;

    if (!PyDict_Check(map))
    {
        PyErr_SetString(C_RENDERER_EXCEPTION, "Map is not a dict!");
        return NULL;
    }

    // Create lighting buffer

    create_lighting_buffer(&lighting_buffer, lights, bk_objects, map, &settings, slice_heights, day, &sky_colour_hsv, left_edge, top_edge);

    // Print lit blocks and background

    Py_ssize_t i = 0;
    PyObject *world_x, *column;

    while (PyDict_Next(map, &i, &world_x, &column))
    {
        long world_x_l = PyLong_AsLong(world_x);
        if (!(world_x_l >= left_edge && world_x_l < right_edge))
            continue;

        if (!PyList_Check(column))
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "Column is not a list!");
            return NULL;
        }

        long x = world_x_l - left_edge;

        long slice_height = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(world_x_l)));

        PyObject *iter = PyObject_GetIter(column);
        PyObject *py_pixel;
        long world_y_l = 0;

        while ((py_pixel = PyIter_Next(iter)))
        {
            if (world_y_l >= top_edge && world_y_l < bottom_edge)
            {
                long y = world_y_l - top_edge;
                bool underground = world_y_l > world_gen_height - slice_height;

                wchar_t pixel = PyString_AsChar(py_pixel);
                if (!pixel)
                {
                    PyErr_SetString(C_RENDERER_EXCEPTION, "Cannot get char from pixel!");
                    return NULL;
                }

                PrintableChar printable_char;
                create_pixel(x, y, world_x_l, world_y_l, map, pixel, objects, &lighting_buffer, underground, &sky_colour_rgb, &settings, &printable_char);

                if (settings.terminal_output > 0)
                {
                    if (!terminal_out(&frame, &printable_char, x, y, &settings))
                        return NULL;
                }
            }

            ++world_y_l;
            Py_XDECREF(py_pixel);
        }

        Py_XDECREF(iter);
    }

    if (settings.terminal_output > 0)
    {
        frame.buffer[frame.cur_pos] = L'\0';
        int n_wprintf_written = wprintf(frame.buffer);

        if (n_wprintf_written != frame.cur_pos)
        {
            PyErr_SetString(C_RENDERER_EXCEPTION, "wfprint messed up!");
            return NULL;
        }
        fflush(stdout);
    }

    Py_RETURN_NONE;
}


static PyMethodDef render_c_methods[] = {
    {"render_map", render_map, METH_VARARGS, PyDoc_STR("render_map(map, edges, edges_y, slice_heights, objects, bk_objects, sky_colour, day, lights, settings, redraw_all) -> None")},
    {NULL, NULL}  /* sentinel */
};

PyDoc_STRVAR(module_doc, "The super-duper-fast renderer");

static struct PyModuleDef render_c_module = {
    PyModuleDef_HEAD_INIT,
    "render",
    module_doc,
    -1,
    render_c_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC
PyInit_render_c(void)
{
    PyObject *m = NULL;

    // Create the module and add the functions
    m = PyModule_Create(&render_c_module);
    if (m == NULL)
    {
        Py_XDECREF(m);
    }

    C_RENDERER_EXCEPTION = PyErr_NewException("render_c.RendererException", NULL, NULL);

    return m;
}
