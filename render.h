#define bool int
#define true 1
#define false 0


typedef struct
{
    bool terminal_output;
    bool neopixels_output;
    bool fancy_lights;
    bool colours;
} Settings;


typedef union {
    struct
    {
        float r;
        float g;
        float b;
    };
    struct
    {
        float h;
        float s;
        float v;
    };
} Colour;


typedef struct
{
    wchar_t character;
    Colour fg, bg;
    int style;
} PrintableChar;


typedef struct {
    long x;
    long y;
    long z;
    long radius;
    long width;
    long height;
    Colour rgb;
    Colour hsv;
} Light;


typedef struct
{
    int current_frame;
    long width;
    long height;

    long x;
    long y;

    struct PixelLighting
    {
        Colour background_colour;
        float background_colour_lightness;
        int background_colour_set_on_frame;

        float lightness;
        int lightness_set_on_frame;
    } *screen;
} LightingBuffer;


typedef struct
{
    wchar_t *buffer;
    size_t size;
    size_t cur_pos;
} ScreenBuffer;


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


typedef struct Object
{
    int from_frame;

    long x;
    long y;
    long hierarchy;
    wchar_t key;
    Colour rgb;
    PyObject *model;

    struct Object *next;
} Object;


#define OBJECTS_MAP_SIZE 512

typedef struct
{
    Object objects[OBJECTS_MAP_SIZE];
} ObjectsMap;

