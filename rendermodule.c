#include "Python.h"


typedef struct
{
    wchar_t character;
    wchar_t character_left;
    wchar_t character_right;

    struct colours
    {
        Colour fg, bg;
        int style;
    };
    bool solid;
} BlockData;


char
get_block(long x, long y, PyObject *map)
{
    char result = 0;
    try:
        return map[x][y]
    except (KeyError, IndexError):
        pass

    return result;
}


wchar_t
get_char(long x, long y, PyObject *map, BlockData *pixel)
{
    char left_block_key = get_block(x-1, y, map);
    char right_block_key = get_block(x+1, y, map);
    char below_block_key = get_block(x, y+1, map);

    wchar_t character = pixel->character;

    if (below == 0 || !is_solid(below))
    {
        if (left_block_key != 0 && is_solid(left_block_key) && pixel->character_left != 0)
        {
            character = pixel->character_left;
        }
        else if (right_block_key != 0 && is_solid(right_block_key) && pixel->character_right != 0)
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

void
calc_pixel(long x, long y, long world_x, long world_y, long world_screen_x,
           PyObject *map, PyObject *slice_heights, char pixel_f_key, PyObject *objects, PyObject *bk_objects,
           Colour sky_colour, float day, PyObject *lights, bool fancy_lights, PrintableChar *result):
{
    result->bg.r = -1;
    result->fg.r = -1;

    // If the front block has a bg
    BlockData pixel_f = get_block_data(pixel_f_key);
    if (pixel_f.colours.bg.r >= 0)
    {
        result->bg = get_block_light(x, world_y, world_screen_x, map, slice_heights, lights, day, pixel_f.colours.bg, fancy_lights);
    }
    else
    {
        result->bg = sky(x, world_y, world_screen_x, map, slice_heights, bk_objects, sky_colour, lights, fancy_lights);
    }

    // Get any object
    wchar_t object_char = 0;
    Colour obj_colour;
    get_obj_pixel(x, world_y, objects, &object_char, &obj_colour);

    if (object_char != 0)
    {
        result->character = object_char;
        result->fg = obj_colour;
    }
    else
    {
        result->character = get_char(world_x, world_y, map, &pixel_f);

        if (pixel_f.colours.fg.r >= 0)
        {
            result->fg = get_block_light(x, world_y, world_screen_x, map, slice_heights, lights, day, pixel_f.colours.fg, fancy_lights);
        }
    }

    result->style = pixel_f.colours.style;
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


int
terminal_out(PrintableChar *c, long width)
{
    size_t frame_pos = y * width + x;
    if (last_frame[frame_pos] != c)
    {
        last_frame[frame_pos] = *c;

        char *pixel = colour_str(c->character, rgb(c->bg), rgb(c->fg), x->style);

        size_t added = pos_str(x, y, pixel, frame->buffer[frame->pos]);
        frame->cur_pos += added;
        if (frame->cur_pos >= frame->size)
        {
            printf("Error: Exceeded frame buffer size in terminal_out!\n");
            return -1;
        }
    }

    return 0;
}


int
neopixels_out()
{
    // neopixels.set_pixel(leds, width, height, x, y, fg or bg)
    return 0;
}


static PrintableChar *last_frame;
static ScreenBuffer frame;
static long width = 0;
static long height = 0;

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
        frame->size = width * height * POS_STR_FORMAT_MAX_LEN;
        frame->buffer = (char *)malloc(frame->size);
        if (frame->buffer)
        {
            printf("Error: Could not allocate frame buffer!\n");
            return -1;
        }
        last_frame = (PrintableChar *)malloc(width * height * sizeof(PrintableChar));
    }

    frame->cur_pos = 0;
    return 0;
}


static PyObject *
render_render(PyObject *self, PyObject *args)
{
    PyObject *map;
    long left_edge,
         right_edge,
         top_edge,
         bottom_edge;
    if (!PyArg_ParseTuple(args, "O(ll)(ll):render", &map,
            &left_edge, &right_edge, &top_edge, &bottom_edge))
        return NULL;

    long cur_width = right_edge - left_edge;
    long cur_height = bottom_edge - top_edge;
    setup_frame(cur_width, cur_height);

    if (!PyDict_Check(map))
        return NULL;

    Py_ssize_t i = 0;
    PyObject *world_x, *column;

    while (PyDict_Next(map, &i, &world_x, &column))
    {
        if (!PyList_Check(column))
        {
            printf("column is not a list\n");
            return NULL;
        }

        long world_x_l = PyLong_AsLong(world_x);
        if (!(world_x_l >= left_edge && world_x_l < right_edge))
            continue;

        long x = world_x_l - left_edge;

        PyObject *iter = PyObject_GetIter(column);
        PyObject *pixel;
        long world_y_l = 0;

        while ((pixel = PyIter_Next(iter)))
        {
            if (world_y_l >= top_edge && world_y_l < bottom_edge)
            {
                long y = world_y_l - top_edge;

                PrintableChar printable_char
                calc_pixel(x, y, world_x_l, world_y_l, left_edge,
                    map, slice_heights, pixel, objects, bk_objects,
                    sky_colour, day, lights, fancy_lights, &printable_char);

                if (terminal_output)
                {
                    if (!terminal_out(&printable_char, width))
                        return NULL;
                }

                if (neopixels)
                {
                    if (!neopixels_out(&printable_char))
                        return NULL;
                }
            }

            ++world_y_l;
            Py_XDECREF(pixel);
        }

        printf("\n");
        Py_XDECREF(iter);
    }

    printf(frame->buffer);

    Py_RETURN_NONE;
}


static PyMethodDef render_methods[] = {
    {"foo",             render_foo,         METH_VARARGS,
        render_foo_doc},
    {"bug",             render_bug,         METH_VARARGS,
        PyDoc_STR("bug(o) -> None")},
    {"render_test",     render_render_test, METH_VARARGS,
        PyDoc_STR("render_test(map) -> None")},
    {"render",          render_render,      METH_VARARGS,
        PyDoc_STR("render(map) -> None")},
    {NULL,              NULL}           /* sentinel */
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