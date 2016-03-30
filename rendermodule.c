#include "Python.h"


calc_pixel(long x, long y, long world_x, long world_y, long world_screen_x,
           PyObject *map_, PyObject *slice_heights, char pixel_f, PyObject *objects, PyObject *bk_objects,
           Colour sky_colour, bool day, PyObject *lights, bool fancy_lights):
{
    Colour bg;

    // If the front block has a bg
    if (blocks[pixel_f]['colours']['bg'] is not None)
    {
        bg = get_block_light(x, world_y, world_screen_x, map_, slice_heights, lights, day, blocks[pixel_f]['colours']['bg'], fancy_lights);
    }
    else
    {
        bg = sky(x, world_y, world_screen_x, map_, slice_heights, bk_objects, sky_colour, lights, fancy_lights);
    }

    // Get any object
    object_char, obj_colour = obj_pixel(x, world_y, objects);

    if (object_char)
    {
        char = object_char;
        fg = obj_colour;
    }
    else
    {
        char = get_char(world_x, world_y, map_, pixel_f);

        if (blocks[pixel_f]['colours']['fg'] is not None)
        {
            fg = get_block_light(x, world_y, world_screen_x, map_, slice_heights, lights, day, blocks[pixel_f]['colours']['fg'], fancy_lights);
        }
        else
        {
            fg = None;
        }
    }

    return fg, bg, char, blocks[pixel_f]['colours']['style']
}

void
terminal_out(Color fg, Colour bg, char *character, int style)
{
    // char *pixel = colour_str(
    //     character,
    //     bg = rgb(bg) if bg is not None else None,
    //     fg = rgb(fg) if fg is not None else None,
    //     style = style
    // )

    // this_frame[x, y] = pixel

    // try:
    //     if not last_frame[x, y] == pixel:
    //         // Changed
    //         diff += POS_STR(x, y, pixel)
    // except KeyError:
    //     # Doesn`t exist
    //     diff += POS_STR(x, y, pixel)
}

void
neopixels_out()
{
    // neopixels.set_pixel(leds, width, height, x, y, fg or bg)
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

        PyObject *iter = PyObject_GetIter(column);
        PyObject *pixel;
        long world_y_l = 0;

        while ((pixel = PyIter_Next(iter)))
        {
            if (world_y_l >= top_edge && world_y_l < bottom_edge)
            {
                calc_pixel(pixel);

                if (terminal_output)
                    terminal_out();

                if (neopixels)
                    neopixels_out();
            }

            ++world_y_l;
            Py_XDECREF(pixel);
        }

        printf("\n");
        Py_XDECREF(iter);
    }

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