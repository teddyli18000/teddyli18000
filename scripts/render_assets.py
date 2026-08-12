#!/usr/bin/env python3
"""Render the profile's deterministic light/dark motion system."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT_DIR = Path("C:/Windows/Fonts")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    )
    for candidate in candidates:
        path = FONT_DIR / candidate
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def field(width: int, height: int, phase: float, dark: bool) -> Image.Image:
    y, x = np.mgrid[0:height, 0:width]
    base = np.array([16, 18, 22] if dark else [248, 246, 241], dtype=np.float32)
    canvas = np.empty((height, width, 3), dtype=np.float32)
    canvas[:] = base
    blobs = [
        (0.70 + 0.05 * math.sin(phase), 0.34 + 0.04 * math.cos(phase), (240, 144, 99), 0.31),
        (0.83 + 0.03 * math.cos(phase * 1.1), 0.62 + 0.05 * math.sin(phase * 0.9), (235, 193, 99), 0.29),
        (0.57 + 0.04 * math.sin(phase + 2.0), 0.69 + 0.03 * math.cos(phase), (96, 203, 199), 0.25),
        (0.90 + 0.02 * math.cos(phase + 1.4), 0.22 + 0.04 * math.sin(phase), (157, 126, 205), 0.23),
    ]
    strength = 0.52 if dark else 0.42
    for cx, cy, color, radius in blobs:
        dx = (x / width - cx) / radius
        dy = (y / height - cy) / (radius * 1.25)
        weight = np.exp(-(dx * dx + dy * dy) * 2.1)[..., None] * strength
        canvas = canvas * (1 - weight) + np.array(color, dtype=np.float32) * weight
    # Fine deterministic grain prevents broad GIF gradient banding without reading as noise.
    noise = (
        np.sin(x * 0.47 + y * 0.31)
        + np.cos(x * 0.23 - y * 0.41)
        + np.sin(x * 0.071 + phase)
        + np.cos(y * 0.067 - phase)
    ) * 0.52
    canvas += noise[..., None]
    return Image.fromarray(np.uint8(np.clip(canvas, 0, 255)), "RGB")


def draw_nodes(image: Image.Image, phase: float, dark: bool) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    ink = (235, 237, 235, 105) if dark else (46, 49, 51, 80)
    points = [
        (610, 116), (728, 82), (842, 142), (688, 228), (816, 276), (910, 221), (747, 344)
    ]
    points = [(x + 7 * math.sin(phase + i), y + 5 * math.cos(phase * 0.8 + i)) for i, (x, y) in enumerate(points)]
    links = [(0, 1), (0, 3), (1, 2), (1, 3), (2, 5), (3, 4), (3, 6), (4, 5), (4, 6)]
    for a, b in links:
        draw.line([points[a], points[b]], fill=ink, width=1)
    for i, (x, y) in enumerate(points):
        r = 4 if i != 4 else 6
        fill = (116, 213, 207, 220) if i == 4 else ((240, 243, 240, 180) if dark else (41, 44, 47, 155))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def organic_contour(cx: int, cy: int, rx: int, ry: int, phase: float) -> list[tuple[float, float]]:
    points = []
    for index in range(128):
        angle = index / 128 * math.tau
        radial = (
            1
            + 0.055 * math.sin(angle * 3 + phase * 0.82)
            + 0.026 * math.sin(angle * 5 - phase * 0.55)
        )
        vertical = 1 + 0.035 * math.cos(angle * 4 + phase)
        points.append(
            (
                cx + rx * radial * math.cos(angle),
                cy + ry * radial * vertical * math.sin(angle),
            )
        )
    return points


def offset_alpha(alpha: Image.Image, dx: int, dy: int) -> Image.Image:
    shifted = Image.new("L", alpha.size, 0)
    shifted.paste(alpha, (dx, dy))
    return shifted


def glass_lens(base: Image.Image, phase: float, dark: bool) -> Image.Image:
    width, height = base.size
    cx = int(width * 0.77 + 13 * math.sin(phase))
    cy = int(height * 0.51 + 8 * math.cos(phase * 0.8))
    rx = int(226 + 7 * math.sin(phase * 0.72))
    ry = int(176 + 6 * math.cos(phase * 0.64))
    contour = organic_contour(cx, cy, rx, ry, phase)
    mask = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon(contour, fill=218)
    # A second moving lobe merges into the primary membrane instead of reading as a circle.
    lobe_x = int(cx + 142 + 8 * math.cos(phase * 0.7))
    lobe_y = int(cy - 112 + 7 * math.sin(phase * 0.9))
    md.ellipse((lobe_x - 102, lobe_y - 78, lobe_x + 102, lobe_y + 78), fill=214)
    mask = mask.filter(ImageFilter.GaussianBlur(3.2))

    # A soft cast shadow plus a centered magnification make the lens feel physical.
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(19)).point(lambda p: int(p * 0.20))
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow.putalpha(offset_alpha(shadow_alpha, 8, 11))
    result = Image.alpha_composite(base.convert("RGBA"), shadow)
    scale = 1.15 + 0.012 * math.sin(phase)
    shear = 0.012 * math.sin(phase * 0.8)
    refracted = base.transform(
        base.size,
        Image.Transform.AFFINE,
        (
            1 / scale,
            shear,
            cx * (1 - 1 / scale) - shear * cy,
            -shear * 0.55,
            1 / scale,
            cy * (1 - 1 / scale) + shear * cx * 0.55,
        ),
        resample=Image.Resampling.BICUBIC,
    ).filter(ImageFilter.GaussianBlur(0.8))
    refracted = ImageEnhance.Contrast(refracted).enhance(1.16)
    result.paste(refracted, (0, 0), mask)
    glaze = Image.new("RGBA", base.size, (255, 255, 255, 0))
    glaze.putalpha(mask.point(lambda p: int(p * (0.14 if dark else 0.095))))
    result = Image.alpha_composite(result.convert("RGBA"), glaze)

    outer = mask.filter(ImageFilter.MaxFilter(7))
    inner = mask.filter(ImageFilter.MinFilter(7))
    rim = ImageChops.subtract(outer, inner).filter(ImageFilter.GaussianBlur(0.7))
    cyan = Image.new("RGBA", base.size, (91, 221, 215, 0))
    cyan.putalpha(offset_alpha(rim.point(lambda p: int(p * 0.34)), -2, 0))
    coral = Image.new("RGBA", base.size, (255, 116, 91, 0))
    coral.putalpha(offset_alpha(rim.point(lambda p: int(p * 0.29)), 2, 1))
    result = Image.alpha_composite(result, cyan)
    result = Image.alpha_composite(result, coral)
    rim_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    rim_layer.putalpha(rim.point(lambda p: min(84, int(p * 0.34))))
    result = Image.alpha_composite(result, rim_layer)

    # A moving Fresnel glare tracks only one edge; it is deliberately not a full outline.
    glare_points = [
        contour[index]
        for index in range(128)
        if 0.56 <= (index / 128) <= 0.80
    ]
    glare = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glare, "RGBA")
    gd.line(glare_points, fill=(255, 255, 255, 78), width=10, joint="curve")
    glare = glare.filter(ImageFilter.GaussianBlur(7))
    result = Image.alpha_composite(result, glare)
    draw = ImageDraw.Draw(result, "RGBA")
    crisp_glare = glare_points[4:-5]
    draw.line(crisp_glare, fill=(255, 255, 255, 172), width=2, joint="curve")
    return result.convert("RGB")


def hero_frame(index: int, total: int, dark: bool) -> Image.Image:
    width, height = 960, 420
    phase = index / total * math.tau
    image = field(width, height, phase, dark)
    draw_nodes(image, phase, dark)
    image = glass_lens(image, phase, dark)
    draw = ImageDraw.Draw(image, "RGBA")
    ink = (245, 242, 235, 255) if dark else (29, 32, 36, 255)
    muted = (190, 190, 185, 235) if dark else (90, 86, 81, 235)
    rule = (255, 255, 255, 48) if dark else (29, 32, 36, 32)
    draw.rounded_rectangle((22, 22, 938, 398), radius=28, outline=rule, width=1)
    draw.text((57, 56), "Xinchen Lee", font=font(62, True), fill=ink)
    draw.text((60, 145), "AI, systems, and things", font=font(28, True), fill=ink)
    draw.text((60, 181), "I felt like building.", font=font(28, True), fill=ink)
    draw.line((60, 245, 435, 245), fill=rule, width=1)
    draw.text((60, 270), "small language models  /  AI infrastructure", font=font(15), fill=muted)
    draw.text((60, 298), "robotics & perception  /  human-in-the-loop tools", font=font(15), fill=muted)
    draw.text((60, 350), "FIELD 01  /  LIVE SIGNAL", font=font(11, True), fill=muted)
    return image


def signal_frame(index: int, total: int, dark: bool, sidequest: bool = False) -> Image.Image:
    width, height = 960, 150
    phase = index / total * math.tau
    image = field(width, height, phase + 1.0, dark)
    image = image.filter(ImageFilter.GaussianBlur(8))
    veil = Image.new("RGBA", image.size, (16, 18, 22, 165) if dark else (248, 246, 241, 175))
    image = Image.alpha_composite(image.convert("RGBA"), veil)
    draw = ImageDraw.Draw(image, "RGBA")
    ink = (241, 239, 233, 180) if dark else (35, 38, 41, 145)
    muted = (183, 182, 177, 220) if dark else (101, 97, 91, 215)
    glow = (114, 218, 211, 245) if dark else (214, 105, 78, 235)
    y = 76
    draw.line((44, y, 916, y), fill=ink, width=1)
    for x in [44, 250, 470, 690, 916]:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=ink)
    if sidequest:
        progress = (index / (total - 1))
        x = 470 + progress * 285
        off = -43 * math.sin(progress * math.pi)
        draw.line((470, y, x, y + off), fill=ink, width=1)
        label = "SIDE QUEST / ONE THING BECOMES ANOTHER"
    else:
        x = 44 + (index / (total - 1)) * 872
        off = 0
        label = "GENERATED SIGNAL / STILL RUNNING"
    draw.ellipse((x - 6, y + off - 6, x + 6, y + off + 6), fill=glow)
    draw.ellipse((x - 13, y + off - 13, x + 13, y + off + 13), outline=(*glow[:3], 70), width=2)
    draw.text((44, 111), label, font=font(11, True), fill=muted)
    return image.convert("RGB")


def save_animation(name: str, maker, dark: bool, frames_count: int, duration: int) -> None:
    frames = [maker(index, frames_count, dark) for index in range(frames_count)]
    stem = f"{name}-{'dark' if dark else 'light'}"
    frames[0].save(ASSETS / f"{stem}.png", optimize=True)
    palettes = [
        frame.quantize(
            colors=256,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        for frame in frames
    ]
    palettes[0].save(
        ASSETS / f"{stem}.gif",
        save_all=True,
        append_images=palettes[1:],
        duration=duration,
        loop=0,
        disposal=2,
        optimize=True,
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for dark in (False, True):
        save_animation("hero", hero_frame, dark, 20, 230)
        save_animation("live-signal", signal_frame, dark, 18, 190)
        save_animation(
            "sidequest",
            lambda index, total, theme: signal_frame(index, total, theme, True),
            dark,
            18,
            190,
        )
    print(f"Rendered motion and fallback assets to {ASSETS}")


if __name__ == "__main__":
    main()
