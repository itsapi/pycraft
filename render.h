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
        float g;
        float r;
        float b;
    };
    struct {
        float s;
        float h;
        float v;
    };
    int32_t colour32;
} Colour;


typedef struct
{
    wchar_t character;
    Colour fg, bg;
    int style;
} PrintableChar;


typedef struct
{
    char *buffer;
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
