#!/usr/bin/env python3
"""make.fun bounty entry: cutest-cat-01 (v2).

Draws the cutest cat -- a ginger kitten with a blep (tongue out), a daisy
crown on its head, hugging a smiling blue plush fish, one paw waving --
and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Standard library only (zlib + struct build the PNG bytes by hand; no PIL,
no network). The picture is fully deterministic: the same code always
writes the same bytes, so both graded runs are identical.
"""

import binascii
import math
import os
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
GINGER = (243, 164, 88)
GINGER_DARK = (214, 126, 50)
GINGER_LIGHT = (250, 190, 120)
CREAM = (255, 250, 242)
PINK = (255, 158, 178)
PINK_DARK = (235, 110, 132)
PINK_SOFT = (255, 182, 196)
BROWN = (96, 62, 44)
EYE_DARK = (58, 38, 28)
TONGUE = (255, 125, 155)
FISH = (95, 168, 221)
FISH_DARK = (52, 120, 185)
FISH_LIGHT = (191, 227, 247)
FISH_BELLY = (160, 210, 240)
YELLOW = (255, 205, 80)
LEAF = (110, 180, 110)
WHITE = (255, 255, 255)

# --- canvas ----------------------------------------------------------------
img = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i], img[i + 1], img[i + 2] = color


def blend_px(x, y, color, alpha):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i] = int(color[0] * alpha + img[i] * (1 - alpha))
        img[i + 1] = int(color[1] * alpha + img[i + 1] * (1 - alpha))
        img[i + 2] = int(color[2] * alpha + img[i + 2] * (1 - alpha))


def fill_background():
    """Warm vertical gradient, pale peach at the top to soft apricot below."""
    top = (255, 246, 233)
    bottom = (255, 226, 196)
    for y in range(H):
        t = y / (H - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        row = bytes((r, g, b)) * W
        img[y * W * 3:(y + 1) * W * 3] = row


def fill_ellipse(cx, cy, rx, ry, color, alpha=1.0):
    """Filled ellipse, scanline by scanline."""
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem <= 0:
            continue
        dx = int(rx * math.sqrt(rem))
        x0 = max(0, cx - dx)
        x1 = min(W - 1, cx + dx)
        if alpha >= 1.0:
            row = bytes(color) * (x1 - x0 + 1)
            i = (y * W + x0) * 3
            img[i:i + len(row)] = row
        else:
            for x in range(x0, x1 + 1):
                blend_px(x, y, color, alpha)


def fill_circle(cx, cy, r, color, alpha=1.0):
    fill_ellipse(cx, cy, r, r, color, alpha)


def _edge(ax, ay, bx, by, px, py):
    return (px - ax) * (by - ay) - (py - ay) * (bx - ax)


def fill_triangle(p1, p2, p3, color):
    """Filled triangle via edge functions."""
    xs = [p1[0], p2[0], p3[0]]
    ys = [p1[1], p2[1], p3[1]]
    x0, x1 = max(0, min(xs)), min(W - 1, max(xs))
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    area = _edge(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
    if area == 0:
        return
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            w0 = _edge(p2[0], p2[1], p3[0], p3[1], x, y)
            w1 = _edge(p3[0], p3[1], p1[0], p1[1], x, y)
            w2 = _edge(p1[0], p1[1], p2[0], p2[1], x, y)
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or \
               (w0 <= 0 and w1 <= 0 and w2 <= 0):
                set_px(x, y, color)


def stamp(x, y, r, color):
    fill_circle(int(round(x)), int(round(y)), r, color)


def draw_line(x0, y0, x1, y1, width, color):
    dist = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(dist))
    r = max(1, width // 2)
    for i in range(n + 1):
        t = i / n
        stamp(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, color)


def draw_curve(p0, p1, p2, width, color, steps=48):
    """Quadratic bezier, stamped with circles."""
    r = max(1, width // 2)
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        stamp(x, y, r, color)


def draw_heart(cx, cy, s, color):
    """Small heart: two circles plus a downward triangle."""
    fill_circle(cx - s // 2, cy - s // 4, s // 2, color)
    fill_circle(cx + s // 2, cy - s // 4, s // 2, color)
    fill_triangle((cx - s, cy), (cx + s, cy), (cx, cy + s), color)


def draw_daisy(cx, cy, r):
    """One daisy: six white petals around a yellow centre."""
    for k in range(6):
        ang = math.pi * k / 3.0
        px = cx + int(0.85 * r * math.cos(ang))
        py = cy + int(0.85 * r * math.sin(ang))
        fill_ellipse(px, py, r // 2 + 2, r // 2 + 2, WHITE)
    fill_circle(cx, cy, r // 2 + 1, YELLOW)
    fill_circle(cx, cy, r // 2 - 2, (255, 190, 40))


def draw_fish(cx, cy):
    """A smiling blue plush fish, held across the kitten's chest.

    Head on the left, tail fin on the right, stitched seams and a happy
    closed-eye smile so it reads as a soft toy, not a real fish.
    """
    # tail fin, behind the body: two clearly separated lobes
    fill_triangle((cx + 150, cy - 10), (cx + 222, cy - 68), (cx + 205, cy + 8), FISH_DARK)
    fill_triangle((cx + 150, cy + 10), (cx + 222, cy + 68), (cx + 205, cy - 8), FISH_DARK)
    fill_triangle((cx + 152, cy - 8), (cx + 206, cy - 54), (cx + 192, cy + 4), FISH)
    fill_triangle((cx + 152, cy + 8), (cx + 206, cy + 54), (cx + 192, cy - 4), FISH)
    # dorsal fin on top
    fill_triangle((cx - 20, cy - 62), (cx + 30, cy - 108), (cx + 70, cy - 60), FISH_DARK)
    fill_triangle((cx - 8, cy - 60), (cx + 28, cy - 92), (cx + 58, cy - 58), FISH)
    # body: dark outline, blue, pale belly
    fill_ellipse(cx, cy, 178, 82, FISH_DARK)
    fill_ellipse(cx, cy, 170, 74, FISH)
    fill_ellipse(cx + 10, cy + 32, 130, 38, FISH_BELLY)
    # stitched seams: short dashes along the back and belly
    for sx in range(cx - 130, cx + 130, 26):
        draw_line(sx, cy - 52, sx + 12, cy - 52, 4, FISH_DARK)
    for sx in range(cx - 120, cx + 130, 26):
        draw_line(sx, cy + 52, sx + 12, cy + 52, 4, FISH_DARK)
    # happy closed eyes (upward arcs) and a big smile on the face
    draw_curve((cx - 128, cy - 18), (cx - 118, cy - 30), (cx - 108, cy - 18), 5, BROWN)
    draw_curve((cx - 92, cy - 14), (cx - 82, cy - 26), (cx - 72, cy - 14), 5, BROWN)
    draw_curve((cx - 128, cy + 8), (cx - 100, cy + 30), (cx - 70, cy + 6), 5, BROWN)
    # pink cheek (the side fin is left off: it read as a stray oval
    # on the belly, and the fish is clear without it)
    fill_circle(cx - 138, cy + 12, 12, PINK, alpha=0.8)


# --- the cat ---------------------------------------------------------------
def draw_cat():
    fill_background()

    # soft sun disc behind the cat, so it pops off the background
    fill_circle(512, 430, 360, (255, 222, 178))

    # tiny hearts floating in the corners, for charm
    draw_heart(150, 150, 26, PINK_SOFT)
    draw_heart(878, 168, 20, PINK_SOFT)

    # soft ground shadow
    fill_ellipse(512, 925, 270, 34, (214, 164, 130), alpha=0.45)

    # curled tail, wrapping around the body's right side: one smooth
    # curve out and up, two thin bands, and a cream tip on its end
    draw_curve((680, 840), (860, 850), (860, 700), 58, GINGER)
    draw_line(790, 790, 840, 830, 10, GINGER_DARK)
    draw_line(830, 735, 872, 772, 10, GINGER_DARK)
    fill_circle(860, 700, 30, CREAM)

    # body: darker outline, then ginger, then a cream chest
    fill_ellipse(512, 735, 222, 192, GINGER_DARK)
    fill_ellipse(512, 732, 212, 182, GINGER)
    fill_ellipse(512, 775, 132, 122, CREAM)

    # waving arm: a raised front leg on the viewer's right, waving hello
    draw_curve((660, 780), (760, 720), (790, 620), 52, GINGER)
    # waving paw with pink toe beans tucked inside its top edge,
    # plus bolder motion arcs beside it so the wave reads at a glance
    fill_ellipse(800, 590, 58, 46, GINGER_DARK)
    fill_ellipse(800, 586, 52, 40, GINGER_LIGHT)
    fill_circle(782, 566, 8, PINK_DARK)
    fill_circle(800, 560, 8, PINK_DARK)
    fill_circle(818, 566, 8, PINK_DARK)
    draw_curve((872, 532), (896, 566), (872, 604), 6, GINGER_DARK)
    draw_curve((892, 520), (920, 560), (892, 614), 6, GINGER_DARK)

    # the plush fish, hugged across the chest
    draw_fish(512, 775)

    # ears, with a slight head tilt: the right ear sits a little lower
    fill_triangle((312, 306), (384, 108), (482, 272), GINGER_DARK)
    fill_triangle((542, 272), (640, 132), (712, 306), GINGER_DARK)
    fill_triangle((322, 298), (388, 122), (472, 264), GINGER)
    fill_triangle((552, 264), (636, 146), (702, 298), GINGER)
    # pink inner ears
    fill_triangle((356, 256), (394, 162), (446, 246), PINK)
    fill_triangle((578, 246), (630, 170), (668, 256), PINK)

    # head: darker outline, then ginger
    fill_circle(512, 400, 238, GINGER_DARK)
    fill_circle(512, 400, 228, GINGER)

    # forehead stripes, tucked under the daisy crown
    fill_ellipse(472, 262, 11, 26, GINGER_DARK)
    fill_ellipse(512, 254, 11, 28, GINGER_DARK)
    fill_ellipse(552, 262, 11, 26, GINGER_DARK)

    # daisy crown: five daisies arched across the top of the head,
    # with little green leaves peeking out between them
    fill_ellipse(418, 228, 22, 10, LEAF)
    fill_ellipse(606, 228, 22, 10, LEAF)
    draw_daisy(385, 238, 26)
    draw_daisy(448, 208, 28)
    draw_daisy(512, 196, 30)
    draw_daisy(576, 208, 28)
    draw_daisy(639, 238, 26)

    # cream muzzle
    fill_ellipse(512, 512, 96, 58, CREAM)

    # eyes: big, bright, the right one a touch higher (head tilt)
    for (ex, ey) in ((428, 394), (598, 388)):
        fill_ellipse(ex, ey, 62, 72, BROWN)          # outline
        fill_ellipse(ex, ey, 57, 67, (255, 255, 255))  # white
        fill_ellipse(ex, ey + 4, 36, 46, EYE_DARK)    # iris
        fill_circle(ex - 13, ey - 18, 13, (255, 255, 255))  # sparkle
        fill_circle(ex + 12, ey + 14, 6, (255, 255, 255))   # sparkle 2

    # pink nose: a little upside-down triangle
    fill_triangle((490, 478), (534, 478), (512, 504), PINK_DARK)
    fill_circle(512, 482, 10, PINK_DARK)

    # mouth: a small "w" under the nose
    draw_curve((512, 506), (498, 528), (482, 516), 5, BROWN)
    draw_curve((512, 506), (526, 528), (542, 516), 5, BROWN)

    # blep: a little pink tongue sticking out below the mouth
    fill_ellipse(512, 552, 30, 36, PINK_DARK)
    fill_ellipse(512, 550, 24, 30, TONGUE)
    draw_line(512, 534, 512, 566, 4, PINK_DARK)

    # blush on both cheeks
    fill_ellipse(362, 480, 40, 22, PINK, alpha=0.55)
    fill_ellipse(662, 474, 40, 22, PINK, alpha=0.55)

    # whiskers: three a side, gently curved
    draw_curve((352, 468), (290, 448), (212, 436), 4, BROWN)
    draw_curve((350, 494), (282, 496), (210, 500), 4, BROWN)
    draw_curve((354, 520), (292, 540), (224, 560), 4, BROWN)
    draw_curve((672, 464), (734, 444), (812, 432), 4, BROWN)
    draw_curve((674, 490), (742, 492), (814, 496), 4, BROWN)
    draw_curve((670, 516), (732, 536), (800, 556), 4, BROWN)

    # front paw hugging the fish, with toe lines
    fill_ellipse(418, 838, 64, 42, GINGER_DARK)
    fill_ellipse(418, 834, 58, 36, GINGER_LIGHT)
    draw_line(402, 822, 402, 852, 3, BROWN)
    draw_line(434, 822, 434, 852, 3, BROWN)


# --- PNG writer ------------------------------------------------------------
def _chunk(kind, data):
    crc = binascii.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def encode_png():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += img[y * W * 3:(y + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", idat)
            + _chunk(b"IEND", b""))


def main():
    draw_cat()
    data = encode_png()
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    target.write_bytes(data)
    print(f"wrote {target} ({len(data)} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
