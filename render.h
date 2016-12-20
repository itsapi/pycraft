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
    struct {
        float r;
        float g;
        float b;
    };
    struct {
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

