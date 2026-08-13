#!/usr/bin/env python3
"""Render the profile's compact, deterministic micro-motion assets."""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FRAME_COUNT = 16
FRAME_MS = 600
LIGHT = (249, 247, 242)
DARK = (18, 19, 21)
INK_L = (30, 29, 27)
INK_D = (243, 239, 232)
CORAL = (190, 91, 68)
SAGE = (120, 137, 114)
FONTS = {
    "serif": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "C:/Windows/Fonts/georgia.ttf"],
    "sans": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/SegUIVar.ttf"],
}

def face(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS[kind]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)

def phase(index: int, total: int) -> float:
    return math.tau * index / (total - 1)

def paper(size: tuple[int, int], dark: bool) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, DARK if dark else LIGHT)
    draw = ImageDraw.Draw(image, "RGBA")
    rule = (225, 219, 208, 17) if dark else (80, 70, 58, 12)
    for y in range(38, height, 26):
        draw.line((0, y, width, y), fill=rule, width=1)
    for row in range(7):
        base = height * (0.14 + row * 0.09)
        points = []
        for x in range(-20, width + 20, 20):
            q = x / max(1, width)
            y = base + 1.7 * math.sin(math.tau * q * 0.8 + row * 0.7)
            y += 0.8 * math.sin(math.tau * q * 1.7 + row * 0.33)
            points.append((x, y))
        color = (218, 210, 197, 18) if dark else (92, 80, 65, 14)
        draw.line(points, fill=color, width=1)
    return image

def hero(size: tuple[int, int], dark: bool, index: int, narrow: bool = False) -> Image.Image:
    width, _ = size
    image = paper(size, dark)
    draw = ImageDraw.Draw(image, "RGBA")
    ink = INK_D if dark else INK_L
    if narrow:
        draw.text((28, 25), "Xinchen Lee", font=face("serif", 37), fill=ink + (255,))
        draw.text((30, 90), "AI, systems, and", font=face("sans", 18), fill=ink + (255,))
        draw.text((30, 118), "things I felt like building.", font=face("sans", 18), fill=ink + (255,))
        x0, x1, center_y, amplitude = 235, 420, 60, 17
    else:
        draw.text((66, 45), "Xinchen Lee", font=face("serif", 60), fill=ink + (255,))
        draw.text((70, 143), "AI, systems, and things I felt like building.", font=face("sans", 23), fill=ink + (255,))
        draw.line((70, 194, 390, 194), fill=(235, 228, 216, 62) if dark else (58, 52, 46, 42), width=1)
        x0, x1, center_y, amplitude = 500, 960, 103, 34
    p = phase(index, FRAME_COUNT)
    line = (229, 220, 207) if dark else (76, 68, 60)
    sage = (161, 171, 151) if dark else SAGE
    for row in range(6):
        points = []
        for x in np.linspace(x0, x1, 120):
            q = (x - x0) / (x1 - x0)
            envelope = 0.2 + 0.8 * q
            y = center_y + (row - 2.5) * 5
            y += amplitude * math.sin(math.tau * (q * 0.8) + p * 0.25 + row * 0.18) * envelope
            y += 5 * math.sin(math.tau * q * 1.6 - p * 0.15 + row * 0.4) * envelope
            points.append((x, y))
        draw.line(points, fill=(*(sage if row in (1, 4) else line), 35), width=1)
    travel = (1 - math.cos(p)) / 2
    x = x0 + (x1 - x0) * (0.12 + 0.68 * travel)
    q = (x - x0) / (x1 - x0)
    y = center_y + amplitude * math.sin(math.tau * (q * 0.8) + p * 0.25 + 0.4) * (0.2 + 0.8 * q)
    y += 5 * math.sin(math.tau * q * 1.6 - p * 0.15 + 0.8) * (0.2 + 0.8 * q)
    accent = (224, 128, 98) if dark else CORAL
    radius = 4 if narrow else 5
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=accent + (225,))
    draw.line((x-20, y+6, x-5, y+1), fill=accent + (120,), width=2)
    return image

def millikan(dark: bool, index: int) -> Image.Image:
    image = paper((280, 96), dark)
    draw = ImageDraw.Draw(image, "RGBA")
    ink = (230, 221, 208, 135) if dark else (70, 64, 56, 110)
    accent = (224, 128, 98) if dark else CORAL
    draw.line((34, 22, 246, 22), fill=ink, width=1)
    draw.line((34, 74, 246, 74), fill=ink, width=1)
    for x in range(55, 246, 38):
        draw.line((x, 19, x, 25), fill=ink[:3] + (75,), width=1)
        draw.line((x, 71, x, 77), fill=ink[:3] + (75,), width=1)
    p = phase(index, FRAME_COUNT)
    travel = (1 - math.cos(p)) / 2
    y = 31 + 34 * travel
    x = 140 + 3 * math.sin(2 * p)
    draw.polygon([(x, y-7), (x-5, y), (x, y+6), (x+5, y)], fill=accent + (205,))
    span = 13
    draw.line((x-span, y, x+span, y), fill=ink[:3] + (85,), width=1)
    draw.line((x-span, y-3, x-span, y+3), fill=ink[:3] + (85,), width=1)
    draw.line((x+span, y-3, x+span, y+3), fill=ink[:3] + (85,), width=1)
    return image

def sidequest(dark: bool, index: int) -> Image.Image:
    image = paper((220, 96), dark)
    draw = ImageDraw.Draw(image, "RGBA")
    ink = (230, 221, 208, 130) if dark else (70, 64, 56, 95)
    accent = (224, 128, 98) if dark else CORAL
    ground = 72
    draw.line((12, ground, 208, ground), fill=ink[:3] + (75,), width=1)
    draw.rectangle((105, 57, 124, 72), outline=ink[:3] + (80,), width=1)
    draw.rectangle((124, 51, 143, 72), outline=ink[:3] + (80,), width=1)
    p = phase(index, FRAME_COUNT)
    travel = (1 - math.cos(p)) / 2
    x = 28 + 153 * travel
    hop = 31 * math.exp(-((x - 126) / 42) ** 2)
    y = ground - 14 - hop
    width, height = 36, 25
    fill = (35, 36, 38, 255) if dark else (252, 249, 243, 255)
    draw.rounded_rectangle((x-width/2, y-height/2, x+width/2, y+height/2), radius=4, fill=fill, outline=accent + (190,), width=1)
    draw.line((x-width/2+5, y-height/2+7, x+width/2-5, y-height/2+7), fill=ink[:3] + (105,), width=1)
    draw.ellipse((x-width/2+5, y-height/2+2, x-width/2+7, y-height/2+4), fill=accent + (150,))
    return image

def save(name: str, frames: list[Image.Image]) -> None:
    ASSETS.mkdir(exist_ok=True)
    first = frames[0].quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    first.save(ASSETS / f"{name}.png", optimize=True)
    palette = frames[0].quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(ASSETS / f"{name}.gif", save_all=True, append_images=indexed[1:], duration=FRAME_MS, loop=0, disposal=1, optimize=True)

def main() -> None:
    for dark in (False, True):
        suffix = "dark" if dark else "light"
        save(f"hero-{suffix}", [hero((960, 300), dark, i) for i in range(FRAME_COUNT)])
        save(f"hero-narrow-{suffix}", [hero((420, 180), dark, i, True) for i in range(FRAME_COUNT)])
        save(f"millikan-mark-{suffix}", [millikan(dark, i) for i in range(FRAME_COUNT)])
        save(f"sidequest-{suffix}", [sidequest(dark, i) for i in range(FRAME_COUNT)])
    print("Rendered compact human-motion assets")

if __name__ == "__main__":
    main()
