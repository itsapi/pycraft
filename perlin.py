repeat = 100

# Hash lookup table as defined by Ken Perlin.  This is a randomly arranged array of all numbers from 0-255 inclusive.
permutation = [
    151, 160, 137,  91,  90,  15, 131,  13, 201,  95,  96,  53, 194, 233,   7, 225,
    140,  36, 103,  30,  69, 142,   8,  99,  37, 240,  21,  10,  23, 190,   6, 148,
    247, 120, 234,  75,   0,  26, 197,  62,  94, 252, 219, 203, 117,  35,  11,  32,
     57, 177,  33,  88, 237, 149,  56,  87, 174,  20, 125, 136, 171, 168,  68, 175,
     74, 165,  71, 134, 139,  48,  27, 166,  77, 146, 158, 231,  83, 111, 229, 122,
     60, 211, 133, 230, 220, 105,  92,  41,  55,  46, 245,  40, 244, 102, 143,  54,
     65,  25,  63, 161,   1, 216,  80,  73, 209,  76, 132, 187, 208,  89,  18, 169,
    200, 196, 135, 130, 116, 188, 159,  86, 164, 100, 109, 198, 173, 186,   3,  64,
     52, 217, 226, 250, 124, 123,   5, 202,  38, 147, 118, 126, 255,  82,  85, 212,
    207, 206,  59, 227,  47,  16,  58,  17, 182, 189,  28,  42, 223, 183, 170, 213,
    119, 248, 152,   2,  44, 154, 163,  70, 221, 153, 101, 155, 167,  43, 172,   9,
    129,  22,  39, 253,  19,  98, 108, 110,  79, 113, 224, 232, 178, 185, 112, 104,
    218, 246,  97, 228, 251,  34, 242, 193, 238, 210, 144,  12, 191, 179, 162, 241,
     81,  51, 145, 235, 249,  14, 239, 107,  49, 192, 214,  31, 181, 199, 106, 157,
    184,  84, 204, 176, 115, 121,  50,  45, 127,   4, 150, 254, 138, 236, 205,  93,
    222, 114,  67,  29,  24,  72, 243, 141, 128, 195,  78,  66, 215,  61, 156, 180
]

# Doubled permutation to avoid overflow
p = [ permutation[x%256] for x in range(0, 512) ]

# Fade function as defined by Ken Perlin.  This eases coordinate values
# so that they will ease towards integral values.  This ends up smoothing
# the final output.
# 6t^5 - 15t^4 + 10t^3
def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def inc(num):
    num += 1
    if repeat > 0:
        num %= repeat
    return num

def grad(hash, x, y, z):
    return [x+y, -x+y,  x-y, -x-y,  x+z, -x+z,  x-z, -x-z,  y+z, -y+z,  y-z, -y-z,  y+x, -y+z,  y-x, -y-z][hash & 0xF]

# Linear Interpolate
def lerp(a, b, x):
    return a + x * (b - a)

def perlin3(x, y, z):
    if repeat > 0:
        # If we have any repeat on, change the coordinates to their "local" repetitions
        x %= repeat
        y %= repeat
        z %= repeat

    # Calculate the "unit cube" that the point asked will be located in
    # The left bound is ( |_x_|,|_y_|,|_z_| ) and the right bound is that
    # plus 1.  Next we calculate the location (from 0.0 to 1.0) in that cube.
    xi = int(x) & 255
    yi = int(y) & 255
    zi = int(z) & 255
    xf = x - int(x)
    yf = y - int(y)
    zf = z - int(z)

    u = fade(xf)
    v = fade(yf)
    w = fade(zf)

    aaa = p[p[p[    xi ]+    yi ]+    zi ]
    aba = p[p[p[    xi ]+inc(yi)]+    zi ]
    aab = p[p[p[    xi ]+    yi ]+inc(zi)]
    abb = p[p[p[    xi ]+inc(yi)]+inc(zi)]
    baa = p[p[p[inc(xi)]+    yi ]+    zi ]
    bba = p[p[p[inc(xi)]+inc(yi)]+    zi ]
    bab = p[p[p[inc(xi)]+    yi ]+inc(zi)]
    bbb = p[p[p[inc(xi)]+inc(yi)]+inc(zi)]

    # The gradient function calculates the dot product between a pseudorandom
    # gradient vector and the vector from the input coordinate to the 8
    # surrounding points in its unit cube.
    x1 = lerp(grad(aaa, xf,   yf,   zf),
              grad(baa, xf-1, yf,   zf),
              u)
    # This is all then lerped together as a sort of weighted average based on the faded(u,v,w)
    # values we made earlier.
    x2 = lerp(grad(aba, xf,   yf-1, zf),
              grad(bba, xf-1, yf-1, zf),
              u)
    y1 = lerp(x1, x2, v)

    x1 = lerp(grad(aab, xf,   yf,   zf-1),
              grad(bab, xf-1, yf,   zf-1),
              u)
    x2 = lerp(grad(abb, xf,   yf-1, zf-1),
              grad(bbb, xf-1, yf-1, zf-1),
              u)
    y2 = lerp(x1, x2, v)

    # For convenience we bind the result to 0 - 1 (theoretical min/max before is [-1, 1])
    return (lerp(y1, y2, w)+1)/2

def perlin2(x, y):
    if repeat > 0:
        # If we have any repeat on, change the coordinates to their "local" repetitions
        x %= repeat
        y %= repeat

    # Calculate the "unit cube" that the point asked will be located in
    # The left bound is ( |_x_|,|_y_|,|_z_| ) and the right bound is that
    # plus 1.  Next we calculate the location (from 0.0 to 1.0) in that cube.
    xi = int(x) & 255
    yi = int(y) & 255
    xf = x - int(x)
    yf = y - int(y)

    u = fade(xf)
    v = fade(yf)

    aa = p[p[    xi ]+    yi ]
    ab = p[p[    xi ]+inc(yi)]
    ba = p[p[inc(xi)]+    yi ]
    bb = p[p[inc(xi)]+inc(yi)]

    # The gradient function calculates the dot product between a pseudorandom
    # gradient vector and the vector from the input coordinate to the 8
    # surrounding points in its unit cube.
    x1 = lerp(grad(aa, xf,   yf,   0),
              grad(ba, xf-1, yf,   0),
              u)
    # This is all then lerped together as a sort of weighted average based on the faded(u,v,0)
    # values we made earlier.
    x2 = lerp(grad(ab, xf,   yf-1, 0),
              grad(bb, xf-1, yf-1, 0),
              u)
    y1 = lerp(x1, x2, v)

    # theoretical min/max is [-1, 1])
    return y1

def OctavePerlin3(x, y, z, octaves, persistence):
    total = 0
    frequency = 1
    amplitude = 1
    # Used for normalizing result to 0.0 - 1.0
    maxValue = 0
    for i in range(0, octaves):
        total += perlin3(x * frequency, y * frequency, z * frequency) * amplitude

        maxValue += amplitude

        amplitude *= persistence
        frequency *= 2

    return total/maxValue
