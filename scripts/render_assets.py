#!/usr/bin/env python3
"""Render the profile's Living Editorial Field raster assets.

The renderer deliberately keeps the atmosphere broad and quiet: typography
is the subject, the fibre field is edge-to-edge material, and a single small
coral accent supplies the only coloured event.  All animated variants share a
12.6 second fundamental cycle and use phase-closed frames so the loop has no
reset seam.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT_DIR = Path("C:/Windows/Fonts")
SOURCE_PLATE = ASSETS / "hero-field-source.jpg"

FRAME_COUNT = 28
FRAME_DURATION_MS = 450
HERO_SIZE = (960, 300)
NARROW_SIZE = (420, 180)
MILLIKAN_SIZE = (960, 56)
SIDEQUEST_SIZE = (960, 70)

LIGHT_BACKGROUND = (247, 244, 238)
DARK_BACKGROUND = (16, 18, 22)
LIGHT_INK = (29, 32, 36, 255)
DARK_INK = (245, 242, 235, 255)
CORAL = (216, 107, 79)


def font(size: int, semibold: bool = False) -> ImageFont.FreeTypeFont:
    """Use a restrained system face with explicit optical tracking in drawing."""
    candidates = (
        ("seguisb.ttf", "SegUIVar.ttf", "arialbd.ttf")
        if semibold
        else ("SegUIVar.ttf", "segoeui.ttf", "arial.ttf")
    )
    for candidate in candidates:
        path = FONT_DIR / candidate
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def display_font(size: int) -> ImageFont.FreeTypeFont:
    """Use an installed serif display face for the editorial title."""
    for candidate in ("georgia.ttf", "cambria.ttc", "times.ttf"):
        path = FONT_DIR / candidate
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return font(size)


def tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    face: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    tracking: float = 0.0,
    anchor: str = "la",
) -> None:
    """Draw text with deliberate tracking instead of default text spacing."""
    x, y = xy
    for character in text:
        draw.text((x, y), character, font=face, fill=fill, anchor=anchor)
        box = draw.textbbox((x, y), character, font=face, anchor=anchor)
        x += (box[2] - box[0]) + tracking


def phase_for(index: int, total: int) -> float:
    """Include the exact endpoint so frame zero and the final frame coincide."""
    if total <= 1:
        return 0.0
    return math.tau * index / (total - 1)


def smoothstep(edge_a: float, edge_b: float, value: float) -> float:
    if edge_a == edge_b:
        return 1.0 if value >= edge_b else 0.0
    t = max(0.0, min(1.0, (value - edge_a) / (edge_b - edge_a)))
    return t * t * (3.0 - 2.0 * t)


def event_window(progress: float, start: float, end: float) -> float:
    """A quiet hold, one small event, then a quiet return to the first frame."""
    rise = smoothstep(start, start + 0.07, progress)
    fall = 1.0 - smoothstep(end - 0.07, end, progress)
    return max(0.0, rise * fall)


def fibre_palette(dark: bool) -> tuple[tuple[int, int, int], ...]:
    if dark:
        return (
            (199, 188, 168),
            (146, 164, 151),
            (151, 160, 167),
            (188, 158, 145),
        )
    return (
        (165, 148, 121),
        (131, 155, 141),
        (143, 151, 158),
        (179, 142, 128),
    )


def atmospheric_field(
    width: int,
    height: int,
    phase: float,
    dark: bool,
    fibre_count: int,
) -> Image.Image:
    """Paint a quiet edge-to-edge editorial fibre field.

    Fibres are long, low-contrast and intentionally unconnected.  Their slow
    integer-harmonic drift creates material atmosphere without a bounded focal
    form or schematic structure.
    """
    background = np.array(DARK_BACKGROUND if dark else LIGHT_BACKGROUND, dtype=np.float32)
    yy, xx = np.mgrid[0:height, 0:width]
    u = xx / max(1, width - 1)
    v = yy / max(1, height - 1)

    # A continuous, warped coordinate field produces broad atmospheric colour
    # variation without closed forms or a centre of gravity.  Each channel is
    # intentionally low amplitude: most of the surface remains paper/graphite.
    warp_u = u + 0.045 * np.sin(math.tau * (v * 0.72) + phase)
    warp_u += 0.022 * np.sin(math.tau * (u * 0.31 + v * 0.27) - 2 * phase)
    warp_v = v + 0.038 * np.sin(math.tau * (u * 0.61) - phase)
    warp_v += 0.018 * np.cos(math.tau * (u * 0.22 - v * 0.44) + 2 * phase)
    sand = 0.5 + 0.5 * np.sin(math.tau * (warp_u * 0.46 + warp_v * 0.16) + 0.4 * math.sin(phase))
    sage = 0.5 + 0.5 * np.cos(math.tau * (warp_u * 0.22 - warp_v * 0.62) - phase)
    coral = 0.5 + 0.5 * np.sin(math.tau * (warp_u * 0.73 + warp_v * 0.37) + 2 * phase)
    cool = 0.5 + 0.5 * np.cos(math.tau * (warp_u * 0.18 + warp_v * 0.88) + phase)
    if dark:
        tones = (
            np.array((157, 137, 105), dtype=np.float32),
            np.array((86, 119, 96), dtype=np.float32),
            np.array((132, 91, 78), dtype=np.float32),
            np.array((88, 112, 123), dtype=np.float32),
        )
    else:
        tones = (
            np.array((224, 201, 163), dtype=np.float32),
            np.array((186, 204, 184), dtype=np.float32),
            np.array((227, 171, 148), dtype=np.float32),
            np.array((202, 211, 215), dtype=np.float32),
        )
    canvas = np.broadcast_to(background, (height, width, 3)).copy()
    # Signed blends keep the paper/graphite base visible while letting broad
    # warm, sage, coral, and cool passages breathe through it.  No colour is
    # anchored to a central shape, so the field reads as atmosphere rather than
    # a gradient demo.
    for value, tone, strength in ((sand, tones[0], 0.22), (sage, tones[1], 0.18), (coral, tones[2], 0.11), (cool, tones[3], 0.12)):
        canvas += (tone - background) * (value - 0.5)[..., None] * strength

    image = Image.fromarray(np.uint8(np.clip(canvas, 0, 255)), "RGB").convert("RGBA")
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    palette = fibre_palette(dark)
    for row in range(fibre_count):
        base_y = height * (0.10 + (row + 0.5) * 0.80 / max(1, fibre_count))
        amplitude = 0.85 + (row % 3) * 0.38
        points: list[tuple[float, float]] = []
        for column in range(0, width + 25, 28):
            normalized = column / max(1, width)
            y = base_y + amplitude * math.sin(math.tau * (normalized * 0.74) + phase + row * 0.41)
            y += 0.42 * math.sin(math.tau * (normalized * 1.8) + 2 * phase + row * 0.63)
            # The fibre follows the same broad field rather than defining it.
            y += 1.35 * math.sin(math.tau * (normalized * 0.33 + 0.15) + phase) * (0.25 + 0.75 * normalized)
            points.append((column, y))
        color = palette[row % len(palette)]
        alpha = 5 + (row % 3) * 2
        draw.line(points, fill=(*color, alpha), width=1, joint="curve")

    # Only two almost imperceptible cross-grain strands remain as material cues.
    for strand in range(max(1, fibre_count // 5)):
        x0 = width * (0.21 + strand * 0.51)
        points = []
        for step in range(0, height + 14, 18):
            normalized = step / max(1, height)
            x = x0 + 1.3 * math.sin(math.tau * normalized + 2 * phase + strand)
            x += 0.5 * math.sin(math.tau * normalized * 2.0 + phase)
            points.append((x, step))
        color = palette[(strand + 2) % len(palette)]
        draw.line(points, fill=(*color, 6), width=1, joint="curve")
    image = Image.alpha_composite(image, layer)

    # Fixed, very low-amplitude paper grain prevents a synthetic flat fill
    # while remaining static between frames and therefore cheap in GIFs.
    grain = (
        np.sin(xx * 0.29 + yy * 0.17)
        + np.cos(xx * 0.13 - yy * 0.23)
    ) * 0.26
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
    pixels = np.clip(pixels + grain[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(pixels, "RGB")


def source_field(width: int, height: int, dark: bool, narrow: bool = False) -> Image.Image:
    """Crop and tone-map the supplied material plate for a raster target.

    Cropping happens at source resolution before downsampling.  The desktop
    window keeps the warm middle and only the restrained lower-right ridge;
    narrow uses an independent left-field window so it is a composition, not a
    scaled desktop poster.
    """
    if not SOURCE_PLATE.is_file():
        raise FileNotFoundError(f"missing Hero source plate: {SOURCE_PLATE}")
    source = Image.open(SOURCE_PLATE).convert("RGB")
    source_width, source_height = source.size
    if narrow:
        crop_box = (0, 78, min(850, source_width), min(442, source_height))
    else:
        crop_box = (0, 0, source_width, min(554, source_height))
    crop = source.crop(crop_box)
    # The plate is atmospheric source material, not a paper-swatch showcase.
    crop = crop.filter(ImageFilter.GaussianBlur(0.35))
    crop = ImageEnhance.Contrast(crop).enhance(0.74)
    crop = ImageEnhance.Color(crop).enhance(0.76)
    image = crop.resize((width, height), Image.Resampling.LANCZOS)

    if not dark:
        # A slight lift keeps the source in the same warm editorial family as
        # the README canvas while preserving its sand/sage/coral variation.
        image = ImageEnhance.Brightness(image).enhance(1.015)
        base = np.array(LIGHT_BACKGROUND, dtype=np.uint8)
    else:
        # Dark is a tone map from this exact plate, not an inverted or random
        # second image.  Luma remains graphite; channel residuals retain the
        # plate's low-saturation sand, sage, and coral temperature shifts.
        pixels = np.asarray(image, dtype=np.float32)
        luma = pixels.mean(axis=2, keepdims=True)
        graphite = np.array(DARK_BACKGROUND, dtype=np.float32)
        mapped = graphite + (pixels - 228.0) * 0.36 + (pixels - luma) * 0.34
        image = Image.fromarray(np.uint8(np.clip(mapped, 8, 60)), "RGB")
        base = np.array(DARK_BACKGROUND, dtype=np.uint8)

    # Lower the right-side plate contrast so the ridge reads as a small spatial
    # event rather than a hero object.  The left 58% is intentionally untouched.
    if not narrow:
        overlay = Image.new("RGBA", image.size, (*base, 0))
        alpha = np.zeros((height, width), dtype=np.uint8)
        start = int(width * 0.62)
        for x in range(start, width):
            fade = (x - start) / max(1, width - start)
            alpha[:, x] = np.uint8(255 * 0.32 * fade)
        # Fade is strongest in the ridge's lower-right half, not over text.
        yy = np.arange(height, dtype=np.float32)[:, None] / max(1, height - 1)
        alpha = np.uint8(alpha * (0.40 + 0.60 * yy))
        overlay.putalpha(Image.fromarray(alpha, "L"))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    return image


def _arc_points(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    start: float,
    end: float,
    samples: int = 72,
) -> list[tuple[float, float]]:
    return [
        (
            center_x + radius_x * math.cos(math.radians(start + (end - start) * index / samples)),
            center_y + radius_y * math.sin(math.radians(start + (end - start) * index / samples)),
        )
        for index in range(samples + 1)
    ]


def _refract_arc_neighbourhood(image: Image.Image, points: list[tuple[float, float]], phase: float) -> None:
    """Apply a barely-there local displacement around an open material strip."""
    padding = 18
    min_x = max(0, int(min(point[0] for point in points)) - padding)
    max_x = min(image.width, int(max(point[0] for point in points)) + padding)
    min_y = max(0, int(min(point[1] for point in points)) - padding)
    max_y = min(image.height, int(max(point[1] for point in points)) + padding)
    if max_x <= min_x or max_y <= min_y:
        return
    box = (min_x, min_y, max_x, max_y)
    patch = image.crop(box)
    shear = 0.018 * math.sin(phase)
    shift_x = 2.2 * math.cos(phase)
    shift_y = 1.3 * math.sin(phase)
    displaced = patch.transform(
        patch.size,
        Image.Transform.AFFINE,
        (1.0, shear, -shift_x, -shear * 0.42, 1.0, -shift_y),
        resample=Image.Resampling.BICUBIC,
    )
    local_points = [(x - min_x, y - min_y) for x, y in points]
    mask = Image.new("L", patch.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.line(local_points, fill=74, width=31, joint="curve")
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    image.paste(displaced, box, mask)


def draw_material_accent(image: Image.Image, phase: float, dark: bool, compact: bool = False) -> None:
    """Draw one open refractive strip with restrained Fresnel light and shade."""
    if compact:
        center_x, center_y = 351 + 1.8 * math.sin(phase), 133 + 1.0 * math.cos(phase)
        radius_x, radius_y = 31, 23
        start, end = 205 + 2 * math.sin(phase), 284 + 2 * math.sin(phase)
        alpha = 94 if dark else 78
    else:
        center_x, center_y = 840 + 2.3 * math.sin(phase), 166 + 1.6 * math.cos(phase)
        radius_x, radius_y = 53, 37
        start, end = 201 + 2 * math.sin(phase), 294 + 2 * math.sin(phase)
        alpha = 104 if dark else 82
    points = _arc_points(center_x, center_y, radius_x, radius_y, start, end)
    _refract_arc_neighbourhood(image, points, phase)
    draw = ImageDraw.Draw(image, "RGBA")
    # Dark edge, warm centre, then one transparent highlight: no closed rim.
    shadow = [(x + 1.0, y + 1.2) for x, y in points]
    draw.line(shadow, fill=((24, 29, 30, 70) if dark else (107, 89, 76, 36)), width=2, joint="curve")
    draw.line(points, fill=(*CORAL, alpha), width=2, joint="curve")
    highlight = [(x - 0.8, y - 1.0) for x, y in points[8:-8]]
    draw.line(highlight, fill=((250, 242, 229, 118) if dark else (255, 252, 244, 98)), width=1, joint="curve")


def draw_hero_type(image: Image.Image, dark: bool, narrow: bool = False) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    ink = DARK_INK if dark else LIGHT_INK
    if narrow:
        tracked_text(draw, (30, 34), "Xinchen Lee", display_font(39), ink, tracking=-0.35)
        tracked_text(draw, (32, 96), "AI, systems, and", font(20), ink, tracking=0.05)
        tracked_text(draw, (32, 124), "things I felt like building.", font(20), ink, tracking=0.05)
        return
    # Display tracking is slightly tighter than sentence tracking, with a
    # generous left margin that remains stable at GitHub's 960px source width.
    tracked_text(draw, (72, 65), "Xinchen Lee", display_font(58), ink, tracking=-0.35)
    tracked_text(
        draw,
        (74, 159),
        "AI, systems, and things I felt like building.",
        font(25),
        ink,
        tracking=0.08,
    )


def hero_frame(index: int, total: int, dark: bool) -> Image.Image:
    phase = phase_for(index, total)
    image = source_field(*HERO_SIZE, dark)
    draw_material_accent(image, phase, dark)
    # One tiny token-like event is allowed to appear near the field edge.  It
    # stays small enough to remain an AI clue, never a schematic.
    event = event_window(index / max(1, total - 1), 0.44, 0.62)
    if event > 0.001:
        draw = ImageDraw.Draw(image, "RGBA")
        x = 702 + 12 * event
        y = 184 - 5 * event
        draw.rectangle((x - 1, y - 1, x + 2, y + 2), fill=(*CORAL, int(100 * event)))
    draw_hero_type(image, dark)
    return image


def narrow_hero_frame(index: int, total: int, dark: bool) -> Image.Image:
    phase = phase_for(index, total)
    image = source_field(*NARROW_SIZE, dark, narrow=True)
    draw_material_accent(image, phase, dark, compact=True)
    event = event_window(index / max(1, total - 1), 0.44, 0.62)
    if event > 0.001:
        draw = ImageDraw.Draw(image, "RGBA")
        x = 274 + 8 * event
        y = 147 - 4 * event
        draw.rectangle((x - 1, y - 1, x + 2, y + 2), fill=(*CORAL, int(96 * event)))
    draw_hero_type(image, dark, narrow=True)
    return image


def micro_strip_base(width: int, height: int, phase: float, dark: bool) -> Image.Image:
    return atmospheric_field(width, height, phase, dark, fibre_count=max(2, height // 22))


def millikan_mark_frame(index: int, total: int, dark: bool) -> Image.Image:
    phase = phase_for(index, total)
    image = micro_strip_base(*MILLIKAN_SIZE, phase, dark)
    draw = ImageDraw.Draw(image, "RGBA")
    neutral = (228, 219, 205, 112) if dark else (90, 83, 73, 82)
    # A tiny measurement trajectory: one drop, one baseline, no screenshot or
    # card.  The mark occupies roughly 70px of visual weight in the strip.
    trajectory = [(445, 38), (464, 36), (482, 28), (502, 31), (520, 22)]
    draw.line(trajectory, fill=neutral, width=1, joint="curve")
    draw.line((444, 40, 528, 40), fill=(*neutral[:3], 56), width=1)
    draw.line((463, 36, 463, 43), fill=(*neutral[:3], 62), width=1)
    event = event_window(index / max(1, total - 1), 0.42, 0.67)
    offset = 7 * event
    drop_x, drop_y = 482 + offset, 28 - 1.6 * event
    drop = [
        (drop_x, drop_y - 6),
        (drop_x - 4, drop_y + 1),
        (drop_x, drop_y + 5),
        (drop_x + 4, drop_y + 1),
    ]
    draw.polygon(drop, fill=(*CORAL, 148 if dark else 132))
    return image


def sidequest_frame(index: int, total: int, dark: bool) -> Image.Image:
    phase = phase_for(index, total)
    image = micro_strip_base(*SIDEQUEST_SIZE, phase, dark)
    draw = ImageDraw.Draw(image, "RGBA")
    neutral = (228, 219, 205, 118) if dark else (82, 77, 71, 82)
    baseline_y = 44
    # A short track bends around one tiny obstacle.  It is a physical joke,
    # not a ruler: no terminal ticks, labels, or full-width instrument strip.
    detour = [(684, baseline_y), (738, baseline_y), (756, 31), (775, 29), (794, baseline_y), (846, baseline_y)]
    draw.line(detour, fill=neutral, width=1, joint="curve")
    draw.rectangle((770, baseline_y - 3, 779, baseline_y + 2), fill=(*neutral[:3], 72))
    progress = index / max(1, total - 1)
    # It starts already a little above the rail so the reduced-motion PNG has
    # a readable off-baseline pose; the cycle gives it one unnecessary extra
    # lift before returning to that quiet pose.
    lift = 8 + 9 * event_window(progress, 0.40, 0.70)
    x = 760 + 9 * math.sin(phase)
    y = baseline_y - lift
    # A small paper-like module briefly clears the obstacle and returns; no
    # second path or decorative halo is introduced.
    module = [(x - 6, y - 3), (x + 5, y - 3), (x + 7, y + 3), (x - 5, y + 3)]
    draw.polygon(module, fill=(*CORAL, 156 if dark else 138))
    draw.line((x - 5, y + 4, x + 5, y + 4), fill=(*neutral[:3], 100), width=1)
    return image


def save_animation(
    name: str,
    maker,
    dark: bool,
    size: tuple[int, int],
    frames_count: int = FRAME_COUNT,
    duration: int = FRAME_DURATION_MS,
) -> None:
    frames = [maker(index, frames_count, dark) for index in range(frames_count)]
    stem = f"{name}-{'dark' if dark else 'light'}"
    frames[0].save(ASSETS / f"{stem}.png", optimize=True)
    # Quantize every frame against one palette built from the static first
    # frame.  A shared palette prevents the textured source plate from
    # changing colours across the whole canvas and lets Pillow encode only
    # the local accent/token deltas.
    palette = frames[0].convert("RGB").quantize(
        colors=128,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palettes = [
        frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    palettes[0].save(
        ASSETS / f"{stem}.gif",
        save_all=True,
        append_images=palettes[1:],
        duration=duration,
        loop=0,
        disposal=1,
        optimize=True,
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for dark in (False, True):
        save_animation("hero", hero_frame, dark, HERO_SIZE)
        save_animation("hero-narrow", narrow_hero_frame, dark, NARROW_SIZE)
        save_animation("millikan-mark", millikan_mark_frame, dark, MILLIKAN_SIZE)
        save_animation("sidequest", sidequest_frame, dark, SIDEQUEST_SIZE)
    print(f"Rendered Living Editorial Field assets to {ASSETS}")


if __name__ == "__main__":
    main()
