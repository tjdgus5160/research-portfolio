#!/usr/bin/env python3
"""Draw the OPM Game Boy assets using Pillow and the Python standard library.

Run: /Users/hyeon/.venv/bin/python scripts/gen_gb_assets.py
No input images, installed fonts, network, randomness, or image models are used.
The task's explicit palette and logical grids are the asset design constants.

Subject notes read before drawing: assets/prompts.md (vapour cell, magnetic
shield, optics, machining, detectors, inspection). These are local art briefs,
not scientific citations. Every image is ILLUSTRATIVE, never measurement data.
The cell has a continuous sealed body and a fused, tapered shoulder tip-off;
the shield shows the open ends of three concentric cylindrical shells.
"""

import argparse
from io import BytesIO
import json
from math import isqrt
from pathlib import Path

from PIL import Image, ImageDraw, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "gb"
SCALE = 6
GB0, GB1, GB2, GB3 = range(4)
PALETTE_HEX = {
    "": ("#0D0D0D", "#3A3A3A", "#8A8A8A", "#D7D7D7"),
    "dmg": ("#0F1A0B", "#30452A", "#6B8F5A", "#C6D8A8"),
}
PALETTE_RGB = {
    directory: tuple(tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
                     for value in colours)
    for directory, colours in PALETTE_HEX.items()
}
PALETTE = [channel for rgb in PALETTE_RGB[""] for channel in rgb]
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
FRAME_SIZE = (24, 24)
FRAME_SLICE = 8

# All 42 glyphs are drawn here by hand. Each integer is a five-bit row;
# bit 4 is the leftmost pixel. No font files or Pillow font APIs are involved.
FONT5X7 = {
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b00001, 0b11110],
    "6": [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    "C": [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    "G": [0b01111, 0b10000, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
    "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "I": [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "J": [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
    "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "N": [0b10001, 0b11001, 0b11001, 0b10101, 0b10011, 0b10011, 0b10001],
    "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    "Y": [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    ".": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00110, 0b00110],
    "/": [0b00001, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b10000],
    "-": [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    "+": [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
    "°": [0b01100, 0b10010, 0b10010, 0b01100, 0b00000, 0b00000, 0b00000],
    "®": [0b01110, 0b10001, 0b11101, 0b11001, 0b11011, 0b10001, 0b01110],
}

# An original wide, cut-corner display face, separate from the label font.
# 13 columns x 9 rows, drawn at 2 logical pixels per bit in the wordmark.
DISPLAY_GLYPHS = {
    "S": (
        "0111111111110", "1111111111111", "1110000000000",
        "1110000000000", "0111111111110", "0000000000111",
        "0000000000111", "1111111111111", "0111111111110",
    ),
    "H": (
        "1110000000111", "1110000000111", "1110000000111",
        "1110000000111", "1111111111111", "1110000000111",
        "1110000000111", "1110000000111", "1110000000111",
    ),
    "P": (
        "1111111111110", "1111111111111", "1110000000111",
        "1110000000111", "1111111111110", "1110000000000",
        "1110000000000", "1110000000000", "1110000000000",
    ),
}
REGISTERED = (
    "001111100", "010000010", "101110001", "101001001", "101110001",
    "101010001", "101001001", "010000010", "001111100",
)
BINARY_ROWS = ("0101", "1100", "1010", "0011")


def canvas(size, colour=GB3):
    image = Image.new("P", size, colour)
    image.putpalette(PALETTE)
    return image


def mask_for(size, kind, coordinates):
    mask = Image.new("1", size, 0)
    getattr(ImageDraw.Draw(mask), kind)(coordinates, fill=1)
    return mask


def dither(image, mask, low, high, coverage):
    """Integer coverage out of 16; callable coverage is allowed per pixel."""
    pixels, selected = image.load(), mask.load()
    for y in range(image.height):
        for x in range(image.width):
            if selected[x, y]:
                threshold = coverage(x, y) if callable(coverage) else coverage
                assert 0 <= threshold <= 16, "Dither coverage outside 0..16"
                pixels[x, y] = high if BAYER[y % 4][x % 4] < threshold else low


def poly(image, points, fill, outline=GB0, width=1):
    draw = ImageDraw.Draw(image)
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=width)


def shadow(image, bounds, coverage=6):
    dither(image, mask_for(image.size, "ellipse", bounds), GB3, GB2, coverage)


def hero(dither_shift=0):
    image = canvas((160, 144))
    # A quiet field: light behind the glass, denser towards the bottom edge.
    field = Image.new("1", image.size, 1)
    dither(image, field, GB3, GB2, lambda x, y: 2 + max(0, y - 48) // 19)
    dither(image, mask_for(image.size, "ellipse", (26, 105, 139, 129)), GB2, GB1, 4)
    dither(image, mask_for(image.size, "ellipse", (43, 108, 124, 119)), GB2, GB1, 10)

    # One closed silhouette: a short fused tip rises from the top shoulder,
    # about 25 degrees right of vertical and one quarter of the body height.
    outer = [
        (56, 40), (79, 40), (82, 35), (87, 24), (89, 22), (92, 22),
        (94, 24), (94, 26), (90, 36), (88, 40), (95, 43), (104, 50), (111, 58),
        (116, 70), (119, 84), (119, 96), (115, 106), (108, 112),
        (94, 115), (60, 115), (47, 111), (39, 104), (35, 94),
        (35, 65), (39, 54), (46, 46),
    ]
    body = mask_for(image.size, "polygon", outer)
    dither(image, body, GB1, GB2,
           lambda x, y: max(4, 15 - max(0, x - 70) // 4)
           + (dither_shift if y >= 44 else 0))  # Keep the fused stem static.
    draw = ImageDraw.Draw(image)
    draw.line(outer + [outer[0]], fill=GB0, width=2)
    poly(image, [(53, 45), (84, 43), (97, 48), (108, 62), (110, 68),
                 (80, 59), (43, 67), (45, 56)], GB2, GB2)
    draw.line([(46, 56), (52, 50), (64, 47), (83, 47), (91, 49)], GB3, 3)
    draw.line([(83, 39), (86, 32), (90, 25)], GB3, 2)
    draw.line([(88, 38), (91, 31), (92, 26)], GB1, 1)
    draw.point((91, 24), GB2)
    # Side wall and the far edge are visible behind the front optical window.
    draw.line([(98, 55), (108, 66), (113, 80), (113, 97), (108, 105),
               (99, 109), (81, 111)], GB3, 2)
    draw.line([(101, 59), (108, 72), (109, 92), (106, 99)], GB0, 1)
    dither(image, mask_for(image.size, "polygon", [
        (92, 77), (106, 81), (107, 96), (101, 103), (86, 106),
    ]), GB1, GB2, 8 + dither_shift)
    # Broad, closed glass front. A thin wall follows the capsule rather than
    # adding a thick concentric collar that could read as a camera lens.
    front = [(56, 49), (76, 48), (88, 51), (97, 58), (102, 68),
             (104, 91), (101, 101), (95, 107), (82, 111), (60, 111),
             (49, 107), (42, 98), (40, 87), (40, 67), (44, 58)]
    poly(image, front, GB2, GB1)
    window = mask_for(image.size, "polygon", [
        (56, 52), (75, 51), (87, 55), (94, 62), (98, 73),
        (100, 90), (97, 99), (91, 104), (80, 107), (61, 107),
        (50, 103), (45, 95), (43, 85), (43, 68), (47, 60),
    ])
    dither(image, window, GB2, GB3,
           lambda x, y: max(0, min(16, 21 - (y - 52) // 3
                                  - max(0, x - 64) // 3 + dither_shift)))
    # Sparse, unbroken highlight strokes retain the empty-looking interior.
    draw.line([(45, 66), (49, 59), (57, 54), (70, 53)], GB3, 2)
    draw.line([(43, 73), (43, 85), (46, 95), (51, 101)], GB3, 2)
    draw.line([(53, 64), (50, 71), (50, 82)], GB3, 3)
    draw.line([(50, 87), (52, 92)], GB3, 2)
    draw.line([(92, 64), (95, 73), (97, 90), (94, 98)], GB1, 1)
    draw.line([(94, 68), (97, 79), (99, 91)], GB3, 1)
    draw.line([(57, 105), (63, 107), (79, 107), (89, 104)], GB3, 2)
    draw.line([(62, 112), (79, 112), (93, 108)], GB3, 1)
    return image


def optics():
    image = canvas((64, 64))
    shadow(image, (3, 47, 60, 57))
    # Two cut-glass cubes, with explicit cemented diagonal split planes.
    for x, y in ((5, 24), (34, 17)):
        poly(image, [(x, y), (x + 9, y - 7), (x + 24, y - 4), (x + 15, y + 3)], GB3)
        poly(image, [(x + 15, y + 3), (x + 24, y - 4),
                     (x + 24, y + 17), (x + 15, y + 25)], GB1)
        face = [(x, y), (x + 15, y + 3), (x + 15, y + 25), (x, y + 22)]
        poly(image, face, GB2)
        poly(image, [(x + 1, y + 2), (x + 14, y + 5), (x + 14, y + 22)], GB3, GB3)
        draw = ImageDraw.Draw(image)
        draw.line([(x + 1, y + 1), (x + 14, y + 24)], GB0, 1)
        draw.line([(x + 3, y + 2), (x + 16, y - 5)], GB2, 1)
        draw.line([(x + 2, y + 7), (x + 2, y + 17)], GB3, 1)
        draw.line([(x + 17, y + 5), (x + 22, y + 1)], GB2, 1)
        draw.line([(x + 16, y + 22), (x + 22, y + 17)], GB2, 1)
    return image


def cell():
    image = canvas((64, 64))
    shadow(image, (10, 51, 57, 59))
    # Squat sealed capsule; its rounded tip rises from the top shoulder.
    outer = [
        (23, 18), (29, 18), (31, 14), (33, 9), (35, 8), (37, 9),
        (38, 11), (36, 15), (35, 18), (39, 20), (44, 24), (47, 30), (48, 36),
        (48, 47), (45, 52), (39, 55), (23, 55), (17, 53), (13, 48),
        (13, 31), (15, 25), (19, 21),
    ]
    poly(image, outer, GB1)
    inner = [(23, 20), (30, 20), (32, 15), (34, 10), (35, 9),
             (36, 10), (36, 12), (34, 17), (34, 20),
             (39, 22), (41, 24), (45, 32), (46, 45),
             (42, 50), (36, 52), (23, 52), (18, 49), (15, 45),
             (15, 31), (17, 26)]
    poly(image, inner, GB2, GB2)
    glass = mask_for(image.size, "polygon", [
        (24, 23), (32, 23), (38, 25), (41, 31), (42, 42),
        (39, 48), (25, 49), (19, 45), (18, 32), (20, 27),
    ])
    dither(image, glass, GB2, GB3, lambda x, y: max(2, 16 - max(0, x + y - 55)))
    draw = ImageDraw.Draw(image)
    draw.line([(18, 29), (21, 25), (25, 23), (32, 23)], GB3, 2)
    draw.line([(17, 33), (17, 43), (20, 48)], GB3, 2)
    draw.line([(31, 19), (33, 14), (35, 10)], GB3, 1)
    draw.line([(43, 31), (45, 37), (45, 44)], GB3, 1)
    draw.line([(23, 52), (36, 52), (42, 49)], GB3, 1)
    draw.line([(23, 54), (37, 54)], GB0, 1)
    return image


def cad():
    image = canvas((64, 64))
    shadow(image, (6, 43, 61, 59), 8)
    # Integer isometric projection: equal 2:1 slopes on the machined faces.
    poly(image, [(5, 28), (32, 42), (32, 56), (5, 42)], GB2)
    poly(image, [(32, 42), (59, 28), (59, 42), (32, 56)], GB1)
    dither(image, mask_for(image.size, "polygon", [
        (35, 44), (56, 33), (56, 41), (35, 52),
    ]), GB1, GB2, 4)
    poly(image, [(5, 28), (32, 14), (59, 28), (32, 42)], GB2)
    poly(image, [(8, 28), (32, 16), (56, 28), (32, 40)], GB3, GB3)
    draw = ImageDraw.Draw(image)
    draw.line([(6, 30), (31, 43), (58, 29)], GB3, 1)
    draw.line([(7, 41), (29, 52)], GB1, 1)
    draw.line([(33, 45), (33, 53)], GB2, 1)
    # Eight counterbores around a projected bolt circle (no fake dimensions).
    centres = [(32, 20), (42, 22), (46, 28), (42, 34),
               (32, 36), (22, 34), (18, 28), (22, 22)]
    for x, y in centres:
        draw.ellipse((x - 3, y - 2, x + 3, y + 2), fill=GB2)
        draw.ellipse((x - 2, y - 2, x + 2, y + 1), fill=GB0)
        draw.line([(x - 1, y + 2), (x + 1, y + 2)], GB1, 1)
    return image


def detector_sprite():
    sprite = canvas((25, 38))
    draw = ImageDraw.Draw(sprite)
    # The same sprite is stamped twice, including window, die and leads.
    for x in (7, 16):
        draw.rectangle((x, 22, x + 1, 36), fill=GB0)
        draw.line((x, 26, x, 35), fill=GB2)
    draw.ellipse((1, 2, 23, 25), fill=GB0)
    draw.ellipse((2, 3, 22, 24), fill=GB1)
    draw.ellipse((1, 0, 23, 22), fill=GB0)
    draw.ellipse((3, 2, 21, 20), fill=GB2)
    draw.arc((3, 2, 21, 20), 185, 300, fill=GB3, width=1)
    draw.ellipse((5, 4, 19, 18), fill=GB0)
    draw.ellipse((6, 5, 18, 17), fill=GB1)
    draw.line([(7, 9), (8, 7), (11, 6)], GB3, 1)
    draw.rectangle((10, 9, 14, 13), fill=GB0)
    draw.line([(10, 9), (14, 9), (14, 13)], GB2, 1)
    draw.line([(8, 13), (10, 11)], GB2, 1)
    draw.line([(14, 12), (17, 14)], GB2, 1)
    return sprite


def detect():
    image = canvas((64, 64))
    shadow(image, (5, 50, 58, 56))
    sprite = detector_sprite()
    image.paste(sprite, (5, 15))
    image.paste(sprite, (34, 15))
    assert image.crop((5, 15, 30, 53)).tobytes() == image.crop((34, 15, 59, 53)).tobytes()
    return image


def part_sprite():
    sprite = canvas((12, 12), GB1)
    draw = ImageDraw.Draw(sprite)
    draw.ellipse((0, 0, 11, 11), fill=GB0)
    draw.ellipse((1, 1, 10, 10), fill=GB2)
    draw.ellipse((2, 1, 9, 8), fill=GB3)
    draw.ellipse((4, 3, 7, 6), fill=GB0)
    draw.line([(4, 7), (7, 7)], GB1, 1)
    draw.line([(3, 10), (8, 10)], GB1, 1)
    return sprite


def check():
    image = canvas((64, 64))
    draw = ImageDraw.Draw(image)
    draw.rectangle((3, 3, 60, 60), fill=GB0)
    draw.rectangle((5, 5, 58, 58), fill=GB1)
    draw.line([(5, 58), (58, 58), (58, 5)], GB2, 1)
    part = part_sprite()
    present = []
    for row in range(3):
        for column in range(3):
            x, y = 9 + column * 17, 9 + row * 17
            if (column, row) == (1, 1):
                # An empty dark recess with the same footprint as each part.
                draw.ellipse((x, y, x + 11, y + 11), fill=GB0)
                draw.arc((x + 1, y + 1, x + 10, y + 10), 15, 125, fill=GB2)
            else:
                image.paste(part, (x, y))
                present.append((x, y))
    assert len(present) == 8
    assert all(image.crop((x, y, x + 12, y + 12)).tobytes() == part.tobytes()
               for x, y in present)
    return image


def shield():
    image = canvas((96, 96), GB0)
    pixels = image.load()
    # Three cylinder mouths: r=43, 32, 21. Each has a narrow continuous
    # stepped rim and a broad inner wall. Integer radial shading preserves
    # concentric geometry; ordered dither is confined to the wall surfaces.
    for y in range(96):
        for x in range(96):
            dx, dy = 2 * x - 95, 2 * y - 95
            r = isqrt(dx * dx + dy * dy)  # twice the logical radius
            if r >= 88:
                colour = GB0
            elif r >= 84:
                colour = GB1 if dx + dy > 20 else GB2
            elif r >= 66:
                coverage = 3 + (84 - r) // 2
                colour = GB1 if BAYER[y % 4][x % 4] < coverage else GB0
            elif r >= 62:
                colour = GB2 if dx + dy > 20 else GB3
            elif r >= 44:
                coverage = 3 + (62 - r) // 2
                colour = GB2 if BAYER[y % 4][x % 4] < coverage else GB1
            elif r >= 40:
                colour = GB3
            elif r >= 22:
                coverage = 5 + (40 - r) // 2
                colour = GB3 if BAYER[y % 4][x % 4] < coverage else GB2
            else:
                colour = GB3
            pixels[x, y] = colour
    return image


def hero_frames():
    # The still already contains this isolated five-pixel bright cross.
    # Use it as the first orbit position, preserving frame 1 pixel for pixel.
    cluster = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
    halo = ((-2, 0), (2, 0), (0, -2), (0, 2),
            (-1, -1), (1, -1), (-1, 1), (1, 1))
    orbit = ((77, 76), (83, 81), (77, 86), (71, 81))
    shifts = (0, 1, 0, -1)
    still = hero()
    start_x, start_y = orbit[0]
    for offsets, colour in ((cluster, GB3), (halo, GB2)):
        assert all(still.getpixel((start_x + dx, start_y + dy)) == colour
                   for dx, dy in offsets), "hero-sprite.png: still's seed cluster changed"
    frames = []
    for (cx, cy), shift in zip(orbit, shifts):
        image = hero(dither_shift=shift)
        # Remove the seed before moving it; a dark one-pixel halo keeps the
        # same single cross legible against the breathing glass dither.
        for dx, dy in cluster:
            image.putpixel((start_x + dx, start_y + dy), GB2)
        for offsets, colour in ((halo, GB2), (cluster, GB3)):
            for dx, dy in offsets:
                image.putpixel((cx + dx, cy + dy), colour)
        frames.append(image)
    assert frames[0].tobytes() == still.tobytes(), "hero-sprite.png: frame 1 differs from hero()"
    return frames


def detect_frames():
    still = detect()
    frames = []
    # Only the 3x3 die interiors change; package, window, wires and leads stay.
    for active_x in (5, 34):
        image = still.copy()
        ImageDraw.Draw(image).rectangle(
            (active_x + 11, 25, active_x + 13, 27), fill=GB3)
        frames.append(image)
    return frames


def shield_frames():
    still = shield()
    # Rotate the index texture clockwise about the existing half-pixel
    # centre. Copy only the innermost wall, never any of the three rims.
    wall = Image.new("1", still.size, 0)
    for y in range(still.height):
        for x in range(still.width):
            dx, dy = 2 * x - (still.width - 1), 2 * y - (still.height - 1)
            if 22 <= isqrt(dx * dx + dy * dy) < 40:
                wall.putpixel((x, y), 1)
    frames = [still.copy()]
    texture = still
    for _ in range(3):
        texture = texture.transpose(Image.Transpose.ROTATE_270)
        image = still.copy()
        image.paste(texture, (0, 0), wall)
        frames.append(image)
    return frames


def sprite_sheet(render, frame_size, frame_count):
    frames = render()
    assert len(frames) == frame_count, "Sprite has the wrong frame count"
    assert len({frame.tobytes() for frame in frames}) == frame_count, "Duplicate sprite frames"
    width, height = frame_size
    sheet = canvas((width * frame_count, height))
    for index, frame in enumerate(frames):
        assert frame.size == frame_size, f"Frame {index + 1}: wrong logical grid"
        verify_palette(frame, f"Frame {index + 1}", 4, PALETTE_RGB[""])
        sheet.paste(frame, (index * width, 0))
        assert sheet.crop((index * width, 0, (index + 1) * width, height)).tobytes() == frame.tobytes(), "Misaligned sprite frame"
    return sheet


def binary_pixel(x, y):
    """Infinite 8-pixel glyph lattice; the sequence repeats every 32 pixels."""
    column, local_x = divmod(x, 8)
    row, local_y = divmod(y, 8)
    glyph = BINARY_ROWS[row % 4][column % 4]
    if 1 <= local_x <= 5 and local_y < 7:
        if FONT5X7[glyph][local_y] & (1 << (5 - local_x)):
            return GB1
    return GB0


def noise_pixel(x, y):
    # 6/16 = 37.5%, the closest full Bayer threshold to approximately 35%.
    return GB1 if BAYER[y % 4][x % 4] < 6 else GB0


def tile(size, pixel_function):
    image = canvas(size, GB0)
    image.putdata([pixel_function(x, y) for y in range(size[1]) for x in range(size[0])])
    return image


def wordmark():
    image = canvas((120, 24), GB0)
    draw = ImageDraw.Draw(image)
    for index, letter in enumerate("SHP"):
        rows = DISPLAY_GLYPHS[letter]
        assert len(rows) == 9 and all(len(row) == 13 for row in rows)
        # A one-pixel extrusion below the custom bitmaps, then flat lit faces.
        for shadow_pass in (True, False):
            for row, bits in enumerate(rows):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        x, y = 7 + index * 31 + column * 2, 3 + row * 2
                        if shadow_pass:
                            draw.rectangle((x + 1, y + 1, x + 2, y + 2), fill=GB1)
                        else:
                            draw.rectangle((x, y, x + 1, y + 1), fill=GB3 if row < 6 else GB2)
    for y, row in enumerate(REGISTERED):
        for x, bit in enumerate(row):
            if bit == "1":
                draw.point((103 + x, 3 + y), fill=GB2)
    return image


def frame_plain():
    image = canvas(FRAME_SIZE)
    ImageDraw.Draw(image).rectangle(
        (0, 0, image.width - 1, image.height - 1), outline=GB0, width=1)
    return image


def frame_bevel(raised=True):
    image = frame_plain()
    draw = ImageDraw.Draw(image)
    highlight, shadow = (GB3, GB1) if raised else (GB1, GB3)
    right, bottom = image.width - 2, image.height - 2
    # Disjoint one-pixel rules: each diagonal junction belongs to one side.
    # Rotating 180 degrees swaps the sides exactly, including the corners.
    draw.line([(1, bottom - 1), (1, 1), (right, 1)], fill=highlight, width=1)
    draw.line([(right, 2), (right, bottom), (1, bottom)], fill=shadow, width=1)
    return image


def frame_dialog():
    image = canvas(FRAME_SIZE)
    draw = ImageDraw.Draw(image)
    notch = 2
    # Nested square-notched silhouettes give a two-pixel outer rule,
    # one-pixel gap, one-pixel inner rule, then the unchanged GB3 fill.
    for inset, colour in ((0, GB0), (2, GB3), (3, GB1), (4, GB3)):
        left = top = inset
        right, bottom = image.width - 1 - inset, image.height - 1 - inset
        draw.polygon([
            (left + notch, top), (right - notch, top),
            (right - notch, top + notch), (right, top + notch),
            (right, bottom - notch), (right - notch, bottom - notch),
            (right - notch, bottom), (left + notch, bottom),
            (left + notch, bottom - notch), (left, bottom - notch),
            (left, top + notch), (left + notch, top + notch),
        ], fill=colour)
    return image


def corner_marks():
    image = canvas(FRAME_SIZE)
    draw = ImageDraw.Draw(image)
    # Leave the slice boundaries clear so no bracket enters an edge tile.
    for flip_x in (False, True):
        for flip_y in (False, True):
            points = [(image.width - 1 - x if flip_x else x,
                       image.height - 1 - y if flip_y else y)
                      for x, y in ((1, 5), (1, 1), (5, 1))]
            draw.line(points, fill=GB0, width=1)
    return image


ASSETS = (
    ("hero.png", (160, 144), hero, "밀봉된 vapour cell과 짧은 tip-off stem"),
    ("svc-1-optics.png", (64, 64), optics, "대각 접합면이 보이는 광학 cube 두 개"),
    ("svc-2-cell.png", (64, 64), cell, "밀봉된 vapour cell의 정면"),
    ("svc-3-cad.png", (64, 64), cad, "bolt circle 가공 구멍이 있는 isometric block"),
    ("svc-4-detect.png", (64, 64), detect, "동일한 원형 photodiode detector 한 쌍"),
    ("svc-5-check.png", (64, 64), check, "가운데 한 자리가 빈 동일 부품 배열"),
    ("shield.png", (96, 96), shield, "동심으로 겹친 자기 차폐 cylinder 세 개의 끝면"),
    ("binary-tile.png", (32, 32), lambda: tile((32, 32), binary_pixel), "반복되는 0과 1 pixel glyph"),
    ("noise-tile.png", (16, 16), lambda: tile((16, 16), noise_pixel), "Bayer 4×4 ordered dither, 37.5%"),
    ("wordmark.png", (120, 24), wordmark, "직접 그린 SHP pixel wordmark와 작은 ®"),
)

SPRITES = (
    ("hero-sprite.png", (160, 144), 4, hero_frames, "hero.png",
     "고정된 vapour cell 내부의 pixel cluster 순환과 Bayer shading 변화"),
    ("detect-sprite.png", (64, 64), 2, detect_frames, None,
     "좌우 photodiode detector의 active area가 번갈아 밝아지는 한 쌍"),
    ("shield-sprite.png", (96, 96), 4, shield_frames, "shield.png",
     "세 cylinder의 고정된 rim과 가장 안쪽 벽면의 회전하는 Bayer pattern"),
)

FRAMES = (
    ("frame-plain.png", FRAME_SIZE, frame_plain, "단일 외곽선의 기본 9-slice panel", 2),
    ("frame-bevel-out.png", FRAME_SIZE, frame_bevel, "좌상단이 밝은 돌출 9-slice bevel", 3),
    ("frame-bevel-in.png", FRAME_SIZE, lambda: frame_bevel(False), "좌상단이 어두운 함몰 9-slice bevel", 3),
    ("frame-dialog.png", FRAME_SIZE, frame_dialog, "네 모서리에 사각 notch가 있는 이중 9-slice frame", 3),
    ("corner-marks.png", FRAME_SIZE, corner_marks, "네 모서리만 표시하는 L자 viewfinder bracket", 2),
)


def verify_frame_edges(image, name, inset):
    """Check straight edge repeats, corner joins and fill at either scale.

    Each edge is a constant cross-section along its run. Check every phase,
    including the last-to-first repeat seam and the adjoining corner pixels;
    matching endpoints alone would miss a stray pixel inside the edge tile.
    """
    width, height = image.size
    assert width == height == 3 * inset, f"{name}: invalid 9-slice geometry"
    centre = image.crop((inset, inset, 2 * inset, 2 * inset))
    assert set(centre.get_flattened_data()) == {GB3}, f"{name}: centre is not GB3"
    for side, bounds, vertical in (
        ("top", (0, 0, width, inset), False),
        ("bottom", (0, 2 * inset, width, height), False),
        ("left", (0, 0, inset, height), True),
        ("right", (2 * inset, 0, width, height), True),
    ):
        strip = image.crop(bounds)
        if vertical:
            strip = strip.transpose(Image.Transpose.TRANSPOSE)
        edge = strip.crop((inset, 0, 2 * inset, inset))
        profile = edge.crop((0, 0, 1, inset)).tobytes()
        assert edge.crop((inset - 1, 0, inset, inset)).tobytes() == profile, f"{name}: {side} repeat seam breaks"
        assert all(edge.crop((run, 0, run + 1, inset)).tobytes() == profile
                   for run in range(inset)), f"{name}: {side} edge is not continuous along its run"
        for join in (inset - 1, 2 * inset):
            assert strip.crop((join, 0, join + 1, inset)).tobytes() == profile, f"{name}: {side} corner join breaks"
        if name == "corner-marks.png":
            assert set(edge.get_flattened_data()) == {GB3}, f"{name}: {side} edge contains a mark"


def verify_bevel_pair():
    raised, pressed = frame_bevel(), frame_bevel(False)
    assert raised.transpose(Image.Transpose.ROTATE_180).tobytes() == pressed.tobytes(), "Bevel frames are not exact opposing mirrors"
    swap = {GB3: GB1, GB1: GB3}
    for y in range(raised.height):
        for x in range(raised.width):
            inset = min(x, y, raised.width - 1 - x, raised.height - 1 - y)
            before, after = raised.getpixel((x, y)), pressed.getpixel((x, y))
            if inset == 1:
                assert before in swap and after == swap[before], "Bevel inner rule does not swap tones"
            else:
                assert before == after == (GB0 if inset == 0 else GB3), "Bevel swap changes outline or fill"


def verify_palette(image, name, expected_count, palette_rgb):
    assert image.mode == "P", f"{name}: expected an indexed image"
    assert len(palette_rgb) == len(set(palette_rgb)) == 4, f"{name}: expected four distinct palette colours"
    assert image.getpalette() == [channel for rgb in palette_rgb for channel in rgb], f"{name}: wrong palette table"
    assert set(image.get_flattened_data()) <= {GB0, GB1, GB2, GB3}, f"{name}: fifth palette index"
    colours = set(image.convert("RGB").get_flattened_data())
    assert colours <= set(palette_rgb), f"{name}: colour outside the selected palette: {colours}"
    assert len(colours) == expected_count, f"{name}: expected {expected_count} colours, got {len(colours)}"
    assert "transparency" not in image.info, f"{name}: unexpected transparency"
    return len(colours)


def verify_seam(image, pixel_function):
    """Compare a 3x3 repeat with an independently sampled infinite field.

    Matching opposing edge pixels is NOT a seamlessness criterion for a
    dither: the alternating phase must continue across the boundary. This
    checks every pixel across both seams and their intersection, plus a
    negative-coordinate phase shift where glyphs are cut across tile edges.
    """
    width, height = image.size
    repeated = canvas((width * 3, height * 3), GB0)
    for row in range(3):
        for column in range(3):
            repeated.paste(image, (column * width, row * height))
    expected = tile(repeated.size, pixel_function)
    assert repeated.tobytes() == expected.tobytes(), "Tile seam breaks the infinite pattern"
    for y in range(-height, height * 2):
        for x in range(-width, width * 2):
            assert image.getpixel((x % width, y % height)) == pixel_function(x, y), "Tile phase mismatch"


def encode_png(image, size, description):
    info = PngImagePlugin.PngInfo()
    info.add_text("EvidenceClass", "ILLUSTRATIVE")
    info.add_text("Generator", "scripts/gen_gb_assets.py")
    info.add_text("LogicalSize", f"{size[0]}x{size[1]}")
    info.add_text("Scale", str(SCALE))
    info.add_itxt("Description", description)
    stream = BytesIO()
    image.save(stream, format="PNG", bits=2, optimize=False, compress_level=9, pnginfo=info)
    return stream.getvalue()


def export_asset(name, size, render, description, *, frame_count=1, still_name=None,
                 colour_count=None, slice_inset=None):
    logical = render()
    assert logical.size == size, f"{name}: wrong logical grid"
    assert render().tobytes() == logical.tobytes(), f"{name}: nondeterministic renderer"
    count = 2 if name in ("binary-tile.png", "noise-tile.png") else 4
    if colour_count is not None:
        count = colour_count
    verify_palette(logical, name, count, PALETTE_RGB[""])
    if slice_inset is not None:
        verify_frame_edges(logical, name, slice_inset)
    if name == "binary-tile.png":
        verify_seam(logical, binary_pixel)
    if name == "noise-tile.png":
        verify_seam(logical, noise_pixel)
        assert list(logical.get_flattened_data()).count(GB1) == 96, "Wrong Bayer coverage"
    size_out = (size[0] * SCALE, size[1] * SCALE)
    assert size[0] % frame_count == 0, f"{name}: unequal frame widths"
    exported = logical.resize(size_out, Image.Resampling.NEAREST)
    # Apply both palettes to the same index raster so their pixels cannot drift.
    for directory, palette_rgb in PALETTE_RGB.items():
        exported.putpalette([channel for rgb in palette_rgb for channel in rgb])
        encoded = encode_png(exported, size, description)
        assert encoded == encode_png(exported, size, description), f"{name}: unstable PNG encoding"
        # Verify the actual encoded PNG, including EVERY 6x6 pixel block.
        with Image.open(BytesIO(encoded)) as decoded:
            decoded.load()
            assert decoded.size == size_out
            verify_palette(decoded, name, count, palette_rgb)
            if slice_inset is not None:
                verify_frame_edges(decoded, name, slice_inset * SCALE)
            for y in range(size[1]):
                for x in range(size[0]):
                    block = decoded.crop((x * SCALE, y * SCALE, (x + 1) * SCALE, (y + 1) * SCALE))
                    assert set(block.get_flattened_data()) == {logical.getpixel((x, y))}, f"{name}: non-integer pixels"
            assert decoded.info["EvidenceClass"] == "ILLUSTRATIVE"
            if still_name is not None:
                with Image.open(OUTPUT / directory / still_name) as still:
                    first_frame = decoded.crop((0, 0, size_out[0] // frame_count, size_out[1]))
                    assert first_frame.size == still.size, f"{name}: frame 1 and {still_name} sizes differ"
                    assert first_frame.convert("RGB").tobytes() == still.convert("RGB").tobytes(), f"{directory or 'greyscale'}/{name}: frame 1 differs from {still_name}"
        destination = OUTPUT / directory
        destination.mkdir(parents=True, exist_ok=True)
        (destination / name).write_bytes(encoded)
        if frame_count == 1 and slice_inset is None:
            print(f"{name}: logical {size[0]}x{size[1]} -> export {size_out[0]}x{size_out[1]}; "
                  f"{count} colours; {destination.relative_to(ROOT)}/")
    if slice_inset is not None:
        print(f"{name}: logical {size[0]}x{size[1]}; slice inset {slice_inset} "
              f"(export {slice_inset * SCALE}); export {size_out[0]}x{size_out[1]}; "
              f"{count} colours/palette; edge-tiling PASS; assets/gb/ + assets/gb/dmg/")
    if frame_count > 1:
        equality = f"PASS ({still_name}, both palettes)" if still_name else "N/A (alternating active areas)"
        print(f"{name}: {frame_count} frames; logical frame {size[0] // frame_count}x{size[1]}; "
              f"export {size_out[0]}x{size_out[1]}; {count} colours/palette; "
              f"frame-1-equals-still {equality}; assets/gb/ + assets/gb/dmg/")


def export_font():
    expected = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ./-+°®")
    assert set(FONT5X7) == expected, "Missing or unexpected font glyphs"
    assert all(len(rows) == 7 and all(type(row) is int and 0 <= row < 32 for row in rows)
               for rows in FONT5X7.values()), "Invalid 5x7 row bitmask"
    assert len({tuple(rows) for rows in FONT5X7.values()}) == len(expected), "Duplicate glyph bitmaps"
    payload = {
        "name": "SHP 5x7",
        "evidence_class": "ILLUSTRATIVE",
        "width": 5,
        "height": 7,
        "advance": 6,
        "bit_order": "MSB left: bit 4 is x=0, bit 0 is x=4; rows run top to bottom",
        "glyphs": FONT5X7,
    }
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    assert json.loads(encoded)["glyphs"] == FONT5X7
    (OUTPUT / "font5x7.json").write_bytes(encoded)
    print("font5x7.json: logical 5x7/glyph -> export 42 row-bitmask glyphs; "
          f"colours N/A (binary masks); {OUTPUT.relative_to(ROOT)}/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", choices=[entry[0] for entry in ASSETS + SPRITES + FRAMES] + ["font5x7.json"],
                        help="Regenerate one asset in both palettes; omit to regenerate the complete set.")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for entry in ASSETS:
        if args.asset is None or args.asset == entry[0]:
            export_asset(*entry)
    for name, frame_size, frame_count, render, still_name, description in SPRITES:
        if args.asset is None or args.asset == name:
            export_asset(name, (frame_size[0] * frame_count, frame_size[1]),
                         lambda: sprite_sheet(render, frame_size, frame_count), description,
                         frame_count=frame_count, still_name=still_name)
    if args.asset is None or args.asset in ("frame-bevel-out.png", "frame-bevel-in.png"):
        verify_bevel_pair()
    for name, size, render, description, colour_count in FRAMES:
        if args.asset is None or args.asset == name:
            export_asset(name, size, render, description, colour_count=colour_count,
                         slice_inset=FRAME_SLICE)
    if args.asset is None or args.asset == "font5x7.json":
        export_font()


if __name__ == "__main__":
    main()
