
#define BLACK         (Colour){{0,         0,         0}}
#define RED           (Colour){{2.0f/3.0f, 0,         0}}
#define GREEN         (Colour){{0,         2.0f/3.0f, 0}}
#define YELLOW        (Colour){{2.0f/3.0f, 1.0f/3.0f, 0}}
#define BLUE          (Colour){{0,         0,         2.0f/3.0f}}
#define MAGENTA       (Colour){{2.0f/3.0f, 0,         2.0f/3.0f}}
#define CYAN          (Colour){{0,         2.0f/3.0f, 2.0f/3.0f}}
#define GRAY          (Colour){{2.0f/3.0f, 2.0f/3.0f, 2.0f/3.0f}}
#define DARK_GRAY     (Colour){{1.0f/3.0f, 1.0f/3.0f, 1.0f/3.0f}}
#define LIGHT_RED     (Colour){{1,         1.0f/3.0f, 1.0f/3.0f}}
#define LIGHT_GREEN   (Colour){{1.0f/3.0f, 1,         1.0f/3.0f}}
#define LIGHT_YELLOW  (Colour){{1,         1,         1.0f/3.0f}}
#define LIGHT_BLUE    (Colour){{1.0f/3.0f, 1.0f/3.0f, 1}}
#define LIGHT_MAGENTA (Colour){{1,         1.0f/3.0f, 1}}
#define LIGHT_CYAN    (Colour){{1.0f/3.0f, 1,         1}}
#define WHITE         (Colour){{1,         1,         1}}


enum
{
    NORMAL,
    BOLD,
    DARK,
    ITALICS,
    UNDERLINE,
    _NULL_STYLE_A,
    _NULL_STYLE_B,
    INVERT,
    CLEAR,
    STRIKETHROUGH
};


bool
colour_eq(Colour *a, Colour *b)
{
    float error = 0.001;
    return (abs(a->r - b->r) <= error &&
            abs(a->g - b->g) <= error &&
            abs(a->b - b->b) <= error);
}


float
lerp(float a, float s, float b)
{
    return a * (1 - s) + (b * s);
}

Colour
lerp_colour(Colour *a, float s, Colour *b)
{
    return (Colour) {
        .r = lerp(a->r, s, b->r),
        .g = lerp(a->g, s, b->g),
        .b = lerp(a->b, s, b->b)
    };
}

Colour
rgb_to_hsv(Colour *rgb)
{
    Colour hsv;

    float min = fmin(rgb->r, fmin(rgb->g, rgb->b));
    float max = fmax(rgb->r, fmax(rgb->g, rgb->b));
    hsv.v = max;

    float delta = max - min;

    if (max != 0)
    {
        hsv.s = delta / max;

        if (delta == 0)
            hsv.h = 0;
        else if (rgb->r == max)
            hsv.h = (rgb->g - rgb->b) / delta;      // between yellow & magenta
        else if (rgb->g == max)
            hsv.h = 2 + (rgb->b - rgb->r) / delta;  // between cyan & yellow
        else
            hsv.h = 4 + (rgb->r - rgb->g) / delta;  // between magenta & cyan

        hsv.h *= 60.0f;

        if (hsv.h < 0)
            hsv.h += 360;
    }
    else
    {
        hsv.s = 0;
        hsv.h = -1;
    }

    return hsv;
}

Colour
hsv_to_rgb(Colour *hsv)
{
    Colour rgb;

    int i;
    float f, p, q, t;

    if (hsv->s == 0)
    {
        rgb.r = rgb.g = rgb.b = hsv->v;  // Grey
        return rgb;
    }

    float h = hsv->h / 60.0f;
    i = floor(h);
    f = h - i;
    p = hsv->v * (1.0f - hsv->s);
    q = hsv->v * (1.0f - hsv->s * f);
    t = hsv->v * (1.0f - hsv->s * (1.0f - f));

    switch (i) {
        case 0:
            rgb.r = hsv->v;
            rgb.g = t;
            rgb.b = p;
            break;
        case 1:
            rgb.r = q;
            rgb.g = hsv->v;
            rgb.b = p;
            break;
        case 2:
            rgb.r = p;
            rgb.g = hsv->v;
            rgb.b = t;
            break;
        case 3:
            rgb.r = p;
            rgb.g = q;
            rgb.b = hsv->v;
            break;
        case 4:
            rgb.r = t;
            rgb.g = p;
            rgb.b = hsv->v;
            break;
        default:
            rgb.r = hsv->v;
            rgb.g = p;
            rgb.b = q;
            break;
    }

    return rgb;
}


int
grey(float value)
{
    return 232 + (int)(value * 23.0f);
}


int
rgb(Colour *c)
{
    int rgb;
    if (c->r == c->g && c->g == c->b)
    {
        rgb = grey(c->r);
    }
    else
    {
        rgb = 16 + (int)(c->r*5.0f)*36 + (int)(c->g*5.0f)*6 + (int)(c->b*5.0f);
    }

    return rgb;
}


#define S_BG_CODE L"\033[48;5;%dm"
#define BG_CODE_MAX_LEN (sizeof(S_BG_CODE) + 1)
static wchar_t *BG_CODE = S_BG_CODE;
#define S_FG_CODE L"\033[38;5;%dm"
#define FG_CODE_MAX_LEN (sizeof(S_FG_CODE) + 1)
static wchar_t *FG_CODE = S_FG_CODE;
#define S_STYLE_CODE L"\033[%dm"
#define STYLE_CODE_MAX_LEN (sizeof(S_STYLE_CODE))
static wchar_t *STYLE_CODE = S_STYLE_CODE;
#define S_COLOUR_END_CODE L"%C\033[0m"
#define COLOUR_END_CODE_MAX_LEN (sizeof(S_COLOUR_END_CODE))
static wchar_t *COLOUR_END_CODE = S_COLOUR_END_CODE;

size_t COLOUR_CODE_MAX_LEN = BG_CODE_MAX_LEN + FG_CODE_MAX_LEN + STYLE_CODE_MAX_LEN + COLOUR_END_CODE_MAX_LEN;

int
colour_str(PrintableChar *c, wchar_t *result, Settings *settings)
{
    int added = 0;

    if (settings->colours)
    {
        if (c->bg.r >= 0)
        {
            int bg = rgb(&(c->bg));
            added += swprintf(result + added, BG_CODE_MAX_LEN, BG_CODE, bg);
        }

        if (c->fg.r >= 0)
        {
            int fg = rgb(&(c->fg));
            added += swprintf(result + added, FG_CODE_MAX_LEN, FG_CODE, fg);
        }

        if (c->style >= 0)
        {
            added += swprintf(result + added, STYLE_CODE_MAX_LEN, STYLE_CODE, c->style);
        }

        added += swprintf(result + added, COLOUR_END_CODE_MAX_LEN, COLOUR_END_CODE, c->character);
    }
    else
    {
        *(result + added) = c->character;
        added += 1;
    }

    return added;
}
