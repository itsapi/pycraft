#include <Python.h>
#include <math.h>

#define bool int
#define true 1
#define false 0

#include "colours.c"


typedef struct
{
    bool terminal_output;
    bool neopixels_output;
    bool fancy_lights;
} Settings;


typedef struct
{
    wchar_t character;
    wchar_t character_left;
    wchar_t character_right;

    struct
    {
        Colour fg, bg;
        int style;
    } colours;
    bool solid;
} BlockData;

static long world_gen_height = 10;


char
PyString_AsChar(PyObject *str)
{
    char result = 0;
    Py_ssize_t size;
    wchar_t *chars = PyUnicode_AsWideCharString(str, &size);
    if (chars && size > 0)
    {
        result = *chars;
    }
    return result;
}


char
get_block(long x, long y, PyObject *map)
{
    char result = 0;

    PyObject *column = PyDict_GetItem(map, PyLong_FromLong(x));
    if (column)
    {
        PyObject *block = PyList_GetItem(column, x);
        if (block)
        {
            result = PyString_AsChar(block);
        }
    }

    return result;
}


BlockData *
get_block_data(char block_key)
{
    return (BlockData *)0;
}


float
lightness(Colour *rgb)
{
    return 0.2126 * rgb->r + 0.7152 * rgb->g + 0.0722 * rgb->b;
}


float
circle_dist(long test_x, long test_y, long x, long y, long r)
{
    return ( pow(test_x - x, 2) / pow(r   , 2) +
             pow(test_y - y, 2) / pow(r*.5, 2) );
}


int
light_mask(long x, long y, PyObject *map, PyObject *slice_heights)
{
    PyObject *px = PyLong_FromLong(x);
    long slice_height = PyLong_AsLong(PyDict_GetItem(slice_heights, px));
    return (get_block_data(get_block(x, y, map))->solid || (world_gen_height - y) < slice_height) ? 0 : -1;
}


float
lit(long x, long y, PyObject *light)
{
    PyObject *lx = PyDict_GetItemString(light, "x"),
             *ly = PyDict_GetItemString(light, "y"),
             *radius = PyDict_GetItemString(light, "radius");

    return fmin(circle_dist(x, y, PyLong_AsLong(lx), PyLong_AsLong(ly), PyLong_AsLong(radius)), 1);
}


void
get_block_lights(long x, long y, PyObject *lights, bool *bitmap)
{
    // Get all lights which affect this pixel
    long i = 0;
    PyObject *iter = PyObject_GetIter(lights);
    PyObject *pixel;

    while ((pixel = PyIter_Next(iter)))
    {
        bitmap[i] = lit(x, y, pixel) < 1;
        ++i;
    }
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


float
get_block_lightness(long x, long y, long world_x, PyObject *map, PyObject *slice_heights, PyObject *lights)
{
    bool bitmap[PyList_Size(lights)];
    get_block_lights(x, y, lights, bitmap);

    float min = 1;
    int i = 0;
    PyObject *iter = PyObject_GetIter(lights);
    PyObject *light;

    // If the light is not hidden by the mask
    while ((light = PyIter_Next(iter)))
    {
        long lx = PyLong_AsLong(PyDict_GetItemString(light, "x"));
        long ly = PyLong_AsLong(PyDict_GetItemString(light, "y"));
        long z = PyLong_AsLong(PyDict_GetItemString(light, "z"));
        Colour rgb = PyColour_AsColour(PyDict_GetItemString(light, "colour"));

        bitmap[i] = bitmap[i] || z >= light_mask(world_x + lx, ly, map, slice_heights);

        float block_lightness = lit(x, y, light) * lightness(&rgb);
        if (bitmap[i] && block_lightness < min)
            min = block_lightness;

        ++i;
    }

    return 1 - min;
}


Colour
get_block_light(long x, long y, long world_x, PyObject *map, PyObject *slice_heights,
                PyObject *lights, float day, Colour *block_colour, Settings *settings)
{
    Colour result;
    if (settings->fancy_lights)
    {
        float block_lightness = get_block_lightness(x, y, world_x, map, slice_heights, lights);
        float d_ground_height = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(world_x+x))) - (world_gen_height - y);
        float v = lerp(day, fmin(1, fmax(0, d_ground_height / 3)), 0);

        Colour hsv = rgb_to_hsv(block_colour);
        hsv.v = lerp(0, fmax(v, block_lightness), hsv.v);
        result = hsv_to_rgb(&hsv);
    }
    return result;
}


Colour
get_light_colour(long x, long y, long world_x, PyObject *map, PyObject *slice_heights, PyObject *lights, Colour *colour_behind_hsv, Settings *settings)
{
    Colour result;
    result.r = -1;

    float slice_height = PyFloat_AsDouble(PyDict_GetItem(slice_heights, PyLong_FromLong(world_x + x)));
    if ((world_gen_height - y) < slice_height)
    {
        result.r = .1;
        result.g = .1;
        result.b = .1;
        if (settings->fancy_lights)
        {
            float block_lightness = get_block_lightness(x, y, world_x, map, slice_heights, lights);
            result.r = (result.r + block_lightness) * .5;
            result.g = (result.g + block_lightness) * .5;
            result.b = (result.b + block_lightness) * .5;
        }
    }
    else
    {
        if (settings->fancy_lights)
        {
            bool bitmap[PyList_Size(lights)];
            get_block_lights(x, y, lights, bitmap);

            // Calculate light level for each light source
            int i = 0;
            PyObject *iter = PyObject_GetIter(lights);
            PyObject *light;
            long max_light_level = -1;
            Colour max_light_level_colour = {};

            while ((light = PyIter_Next(iter)))
            {
                if (bitmap[i])
                {
                    float light_distance = PyFloat_AsDouble(PyDict_GetItemString(light, "distance"));

                    Colour light_colour_rgb = PyColour_AsColour(PyDict_GetItemString(light, "colour"));
                    Colour light_colour_hsv = rgb_to_hsv(&light_colour_rgb);

                    Colour this_light_pixel_colour_hsv = lerp_colour(&light_colour_hsv, light_distance, colour_behind_hsv);
                    Colour this_light_pixel_colour_rgb = hsv_to_rgb(&this_light_pixel_colour_hsv);
                    long light_level = lightness(&this_light_pixel_colour_rgb);

                    if (light_level > max_light_level)
                        max_light_level = light_level;
                        max_light_level_colour = this_light_pixel_colour_rgb;
                }
                ++i;
            }

            // Get brightest light
            if (max_light_level >= 0)
            {
                result = max_light_level_colour;
            }
            else
            {
                result = hsv_to_rgb(colour_behind_hsv);
            }
        }
        else
        {
            result = *colour_behind_hsv;

            PyObject *iter = PyObject_GetIter(lights);
            PyObject *light;

            while ((light = PyIter_Next(iter)))
            {
                if (lit(x, y, light) < 1)
                {
                    result = CYAN;
                    break;
                }
            }
        }
    }

    return result;
}


Colour
sky(long x, long y, long world_x, PyObject *map, PyObject *slice_heights, PyObject *bk_objects, Colour *sky_colour, PyObject *lights, Settings *settings)
{
    Colour result;
    result.r = -1;

    PyObject *iter = PyObject_GetIter(bk_objects);
    PyObject *object;

    while ((object = PyIter_Next(iter)))
    {
        long ox = PyLong_AsLong(PyDict_GetItemString(object, "x"));
        long oy = PyLong_AsLong(PyDict_GetItemString(object, "y"));
        long oz = PyLong_AsLong(PyDict_GetItemString(object, "z"));

        if (oz >= light_mask(world_x + ox, oy, map, slice_heights))
        {
            long o_width= PyLong_AsLong(PyDict_GetItemString(object, "width"));
            long o_height= PyLong_AsLong(PyDict_GetItemString(object, "height"));

            if (x <= ox && ox < (x + o_width) &&
                y <= oy && oy < (y + o_height))
            {
                result = PyColour_AsColour(PyDict_GetItemString(object, "colour"));
                break;
            }
        }
    }

    if (result.r < 0)
    {
        result = get_light_colour(x, y, world_x, map, slice_heights, lights, sky_colour, settings);
    }

    return result;
}


wchar_t
get_char(long x, long y, PyObject *map, BlockData *pixel)
{
    char left_block_key = get_block(x-1, y, map);
    char right_block_key = get_block(x+1, y, map);
    char below_block_key = get_block(x, y+1, map);

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


typedef struct
{
    wchar_t character;
    Colour fg, bg;
    int style;
} PrintableChar;

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
}


void
calc_pixel(long x, long y, long world_x, long world_y, long world_screen_x,
           PyObject *map, PyObject *slice_heights, char pixel_f_key, PyObject *objects, PyObject *bk_objects,
           Colour *sky_colour, float day, PyObject *lights, Settings *settings, PrintableChar *result)
{
    result->bg.r = -1;
    result->fg.r = -1;

    // If the front block has a bg
    BlockData *pixel_f = get_block_data(pixel_f_key);
    if (pixel_f->colours.bg.r >= 0)
    {
        result->bg = get_block_light(x, world_y, world_screen_x, map, slice_heights, lights, day, &(pixel_f->colours.bg), settings);
    }
    else
    {
        result->bg = sky(x, world_y, world_screen_x, map, slice_heights, bk_objects, sky_colour, lights, settings);
    }

    // Get any object
    wchar_t obj_key = 0;
    Colour obj_colour;
    get_obj_pixel(x, world_y, objects, &obj_key, &obj_colour);

    if (obj_key != 0)
    {
        result->character = obj_key;
        result->fg = obj_colour;
    }
    else
    {
        result->character = get_char(world_x, world_y, map, pixel_f);

        if (pixel_f->colours.fg.r >= 0)
        {
            result->fg = get_block_light(x, world_y, world_screen_x, map, slice_heights, lights, day, &(pixel_f->colours.fg), settings);
        }
    }

    result->style = pixel_f->colours.style;
}


typedef struct
{
    char *buffer;
    size_t size;
    size_t cur_pos;
} ScreenBuffer;


#define POS_STR_FORMAT "\033[%ld;%ldH%s"
#define POS_STR_FORMAT_MAX_LEN sizeof(POS_STR_FORMAT)
size_t
pos_str(long x, long y, char *s, char *result)
{
    char format[] = POS_STR_FORMAT;
    return sprintf(result, format, y+1, x+1, s);
}


static PrintableChar *last_frame;
static ScreenBuffer frame;
static long width;
static long height;

int
terminal_out(PrintableChar *c, long x, long y, long width)
{
    size_t frame_pos = y * width + x;
    if (!printable_char_eq(last_frame + frame_pos, c))
    {
        last_frame[frame_pos] = *c;

        char *pixel = colour_str(c->character, c->bg, c->fg, c->style);

        size_t added = pos_str(x, y, pixel, frame.buffer + frame.cur_pos);
        frame.cur_pos += added;
        if (frame.cur_pos >= frame.size)
        {
            printf("Error: Exceeded frame buffer size in terminal_out!\n");
            return 0;
        }
    }

    return 1;
}


int
neopixels_out(PrintableChar *printable_char)
{
    // neopixels.set_pixel(leds, width, height, x, y, fg or bg)
    return 1;
}


int
setup_frame(long new_width, long new_height)
{
    bool resize = false;
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
        frame.size = width * height * POS_STR_FORMAT_MAX_LEN;
        frame.buffer = (char *)malloc(frame.size);
        if (!frame.buffer)
        {
            printf("Error: Could not allocate frame buffer!\n");
            return 0;
        }
        last_frame = (PrintableChar *)malloc(width * height * sizeof(PrintableChar));
    }

    frame.cur_pos = 0;
    return 1;
}


static PyObject *
render_render(PyObject *self, PyObject *args)
{
    long left_edge,
         right_edge,
         top_edge,
         bottom_edge,
         day;
    PyObject *map, *slice_heights, *objects, *bk_objects, *py_sky_colour, *lights, *py_settings;

    if (!PyArg_ParseTuple(args, "O(ll)(ll)OOOOfOO:render", &map,
            &left_edge, &right_edge, &top_edge, &bottom_edge,
            &slice_heights, &objects, &bk_objects, &py_sky_colour, &day, &lights, &py_settings))
        return NULL;

    Colour sky_colour = PyColour_AsColour(py_sky_colour);
    Settings settings;

    long cur_width = right_edge - left_edge;
    long cur_height = bottom_edge - top_edge;
    if (!setup_frame(cur_width, cur_height))
        return NULL;

    if (!PyDict_Check(map))
        return NULL;

    Py_ssize_t i = 0;
    PyObject *world_x, *column;

    while (PyDict_Next(map, &i, &world_x, &column))
    {
        if (!PyList_Check(column))
        {
            printf("Error: Column is not a list!\n");
            return NULL;
        }

        long world_x_l = PyLong_AsLong(world_x);
        if (!(world_x_l >= left_edge && world_x_l < right_edge))
            continue;

        long x = world_x_l - left_edge;

        PyObject *iter = PyObject_GetIter(column);
        PyObject *py_pixel;
        long world_y_l = 0;

        while ((py_pixel = PyIter_Next(iter)))
        {
            if (world_y_l >= top_edge && world_y_l < bottom_edge)
            {
                long y = world_y_l - top_edge;

                char pixel = PyString_AsChar(py_pixel);
                if (pixel)
                {
                    printf("Error: Cannot get char from pixel!\n");
                    return NULL;
                }

                PrintableChar printable_char;
                calc_pixel(x, y, world_x_l, world_y_l, left_edge,
                    map, slice_heights, pixel, objects, bk_objects,
                    &sky_colour, day, lights, &settings, &printable_char);

                if (settings.terminal_output)
                {
                    if (terminal_out(&printable_char, x, y, width))
                        return NULL;
                }

                if (settings.neopixels_output)
                {
                    if (neopixels_out(&printable_char))
                        return NULL;
                }
            }

            ++world_y_l;
            Py_XDECREF(py_pixel);
        }

        strcpy("\n", frame.buffer + frame.cur_pos);
        frame.cur_pos += 1;
        Py_XDECREF(iter);
    }

    fwrite(frame.buffer, frame.cur_pos, 1, stdout);

    Py_RETURN_NONE;
}


static PyMethodDef render_methods[] = {
    {"render", render_render, METH_VARARGS, PyDoc_STR("render(map) -> None")},
    {NULL, NULL}  /* sentinel */
};

PyDoc_STRVAR(module_doc, "The super-duper-fast renderer");

static struct PyModuleDef rendermodule = {
    PyModuleDef_HEAD_INIT,
    "render",
    module_doc,
    -1,
    render_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC
PyInit_render(void)
{
    PyObject *m = NULL;

    /* Create the module and add the functions */
    m = PyModule_Create(&rendermodule);
    if (m == NULL)
        goto fail;

    return m;
 fail:
    Py_XDECREF(m);
    return NULL;
}
