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

# One slow fundamental keeps every animated layer phase-aligned.  Each motion
# term below is an integer harmonic of this phase, so the GIF can loop without
# a last-frame reset or a separately timed layer.
FRAME_COUNT = 20
FRAME_DURATION_MS = 300
HERO_FRAME_COUNT = 32
HERO_FRAME_DURATION_MS = 300
HERO_SIZE = (960, 320)


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
        (0.70 + 0.035 * math.sin(phase), 0.34 + 0.035 * math.cos(2 * phase), (240, 144, 99), 0.31),
        (0.83 + 0.025 * math.cos(2 * phase), 0.62 + 0.040 * math.sin(phase), (235, 193, 99), 0.29),
        (0.57 + 0.030 * math.sin(phase + 2.0), 0.69 + 0.025 * math.cos(3 * phase), (96, 203, 199), 0.25),
        (0.90 + 0.018 * math.cos(2 * phase + 1.4), 0.22 + 0.030 * math.sin(phase), (157, 126, 205), 0.23),
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
        + np.cos(y * 0.067 - 2 * phase)
    ) * 0.52
    canvas += noise[..., None]
    return Image.fromarray(np.uint8(np.clip(canvas, 0, 255)), "RGB")


def bezier_points(
    start: tuple[float, float],
    control_a: tuple[float, float],
    control_b: tuple[float, float],
    end: tuple[float, float],
    samples: int = 48,
) -> list[tuple[float, float]]:
    """Return a small cubic path for the few deliberate signal traces."""
    points = []
    for index in range(samples + 1):
        t = index / samples
        inv = 1 - t
        points.append(
            (
                inv**3 * start[0]
                + 3 * inv**2 * t * control_a[0]
                + 3 * inv * t**2 * control_b[0]
                + t**3 * end[0],
                inv**3 * start[1]
                + 3 * inv**2 * t * control_a[1]
                + 3 * inv * t**2 * control_b[1]
                + t**3 * end[1],
            )
        )
    return points


def organic_contour(cx: int, cy: int, rx: int, ry: int, phase: float) -> list[tuple[float, float]]:
    points = []
    for index in range(128):
        angle = index / 128 * math.tau
        radial = (
            1
            + 0.055 * math.sin(angle * 3 + phase)
            + 0.026 * math.sin(angle * 5 - 2 * phase)
        )
        vertical = 1 + 0.035 * math.cos(angle * 4 + 2 * phase)
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
    cx = int(width * 0.74 + 8 * math.sin(phase))
    cy = int(height * 0.515 + 5 * math.cos(2 * phase))
    rx = int(183 + 5 * math.sin(2 * phase))
    ry = int(164 + 4 * math.cos(phase))
    contour = organic_contour(cx, cy, rx, ry, phase)
    mask = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon(contour, fill=225)
    # Keep one bounded membrane with a visible thickness; a second free lobe
    # would read as the old node network rather than a single refractive field.
    mask = mask.filter(ImageFilter.GaussianBlur(2.4))

    # A soft cast shadow plus a centered magnification make the lens feel physical.
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(19)).point(lambda p: int(p * 0.20))
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow.putalpha(offset_alpha(shadow_alpha, 8, 11))
    result = Image.alpha_composite(base.convert("RGBA"), shadow)
    scale = 1.13 + 0.010 * math.sin(phase)
    shear = 0.009 * math.sin(2 * phase)
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
    refracted = ImageEnhance.Contrast(refracted).enhance(1.14)
    result.paste(refracted, (0, 0), mask)
    glaze = Image.new("RGBA", base.size, (255, 255, 255, 0))
    glaze.putalpha(mask.point(lambda p: int(p * (0.14 if dark else 0.095))))
    result = Image.alpha_composite(result.convert("RGBA"), glaze)

    outer = mask.filter(ImageFilter.MaxFilter(9))
    inner = mask.filter(ImageFilter.MinFilter(9))
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

    # A restrained Fresnel glare tracks only one edge; it is deliberately not a full outline.
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


def lens_geometry(width: int, height: int, phase: float) -> tuple[int, int, int, int]:
    """Match the membrane geometry used by ``glass_lens`` for signal handoff."""
    return (
        int(width * 0.74 + 8 * math.sin(phase)),
        int(height * 0.515 + 5 * math.cos(2 * phase)),
        int(183 + 5 * math.sin(2 * phase)),
        int(164 + 4 * math.cos(phase)),
    )


def draw_input_signals(image: Image.Image, phase: float, dark: bool) -> Image.Image:
    """Draw three quiet inputs that terminate at the membrane's left boundary."""
    width, height = image.size
    cx, cy, rx, _ = lens_geometry(width, height, phase)
    trace = (245, 238, 221, 132) if dark else (55, 57, 58, 100)
    accent = (113, 211, 205, 185) if dark else (193, 92, 73, 145)
    # Inputs stay short and independent; there is no node-to-node background graph.
    offsets = (-64, 0, 58)
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for index, offset in enumerate(offsets):
        start = (cx - rx - 106, cy + offset + 6 * math.sin(phase + index))
        end = (cx - rx + 9, cy + offset + 4 * math.cos(2 * phase + index))
        curve = bezier_points(
            start,
            (start[0] + 39, start[1] - 12 * math.cos(phase + index)),
            (end[0] - 42, end[1] + 10 * math.sin(phase + index)),
            end,
        )
        draw.line(curve, fill=trace, width=2, joint="curve")
        dot_radius = 3 if index != 1 else 4
        draw.ellipse(
            (
                start[0] - dot_radius,
                start[1] - dot_radius,
                start[0] + dot_radius,
                start[1] + dot_radius,
            ),
            fill=accent,
        )
    return Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")


def draw_output_signals(image: Image.Image, phase: float, dark: bool) -> Image.Image:
    """Draw one output and a faint terminal breakaway after the refractive field."""
    width, height = image.size
    cx, cy, rx, _ = lens_geometry(width, height, phase)
    primary = (104, 213, 207, 210) if dark else (193, 87, 69, 175)
    core = (228, 245, 236, 190) if dark else (89, 69, 61, 145)
    start = (cx + rx - 6, cy - 12 + 5 * math.sin(phase))
    end = (946, cy - 29 + 9 * math.cos(2 * phase))
    curve = bezier_points(
        start,
        (start[0] + 42, start[1] - 22 * math.cos(phase)),
        (end[0] - 90, end[1] + 18 * math.sin(phase)),
        end,
        samples=64,
    )
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.line(curve, fill=(*primary[:3], 95), width=13, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    result = Image.alpha_composite(image.convert("RGBA"), glow)
    draw = ImageDraw.Draw(result, "RGBA")
    draw.line(curve, fill=primary, width=3, joint="curve")
    draw.line(curve[8:-6], fill=core, width=1, joint="curve")
    tip_x, tip_y = end
    draw.ellipse((tip_x - 4, tip_y - 4, tip_x + 4, tip_y + 4), fill=primary)

    # A single low-contrast branch appears only at the final third of the output.
    branch_start = curve[-27]
    branch_end = (938, branch_start[1] + 39 + 5 * math.sin(phase))
    branch = bezier_points(
        branch_start,
        (branch_start[0] + 21, branch_start[1] + 3 * math.cos(phase)),
        (branch_end[0] - 38, branch_end[1] - 17 * math.sin(2 * phase)),
        branch_end,
        samples=28,
    )
    branch_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(branch_layer, "RGBA")
    bd.line(branch, fill=(*primary[:3], 68), width=2, joint="curve")
    branch_layer = branch_layer.filter(ImageFilter.GaussianBlur(0.7))
    result = Image.alpha_composite(result, branch_layer)
    return result.convert("RGB")


def editorial_trace_palette(dark: bool) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int, int]]:
    """Return restrained hairline, secondary hairline, and one accent color."""
    if dark:
        return (239, 236, 228, 142), (239, 236, 228, 78), (99, 205, 196)
    return (47, 50, 53, 126), (47, 50, 53, 70), (187, 76, 54)


def sample_polyline(points: list[tuple[float, float]], progress: float) -> tuple[float, float, float, float]:
    """Sample a point and local tangent from a polyline at 0..1 progress."""
    if len(points) < 2:
        raise ValueError("a pulse route needs at least two points")
    progress = max(0.0, min(1.0, progress))
    lengths = [
        math.hypot(points[index + 1][0] - points[index][0], points[index + 1][1] - points[index][1])
        for index in range(len(points) - 1)
    ]
    total = sum(lengths)
    target = total * progress
    travelled = 0.0
    for index, segment_length in enumerate(lengths):
        if travelled + segment_length >= target or index == len(lengths) - 1:
            local = 0.0 if segment_length == 0 else (target - travelled) / segment_length
            x = points[index][0] + local * (points[index + 1][0] - points[index][0])
            y = points[index][1] + local * (points[index + 1][1] - points[index][1])
            tx = points[index + 1][0] - points[index][0]
            ty = points[index + 1][1] - points[index][1]
            return x, y, tx, ty
        travelled += segment_length
    return points[-1][0], points[-1][1], points[-1][0] - points[-2][0], points[-1][1] - points[-2][1]


def smoothstep(edge_a: float, edge_b: float, value: float) -> float:
    if edge_a == edge_b:
        return 1.0 if value >= edge_b else 0.0
    t = max(0.0, min(1.0, (value - edge_a) / (edge_b - edge_a)))
    return t * t * (3.0 - 2.0 * t)


def editorial_trace_frame(index: int, total: int, dark: bool) -> Image.Image:
    """Render the typography-first Editorial Signal Trace hero.

    The drawing is intentionally independent of the older field/lens helpers:
    a few aligned traces route into one main line while the only animated event
    is a quiet pulse that fades in and out at the route's endpoints.
    """
    width, height = HERO_SIZE
    progress = index / total
    background = (17, 19, 23) if dark else (250, 248, 243)
    hairline, secondary, accent = editorial_trace_palette(dark)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image, "RGBA")

    # A precise frame and one short rule give the poster an editorial grid
    # without competing with the two lines of type.
    frame = (255, 255, 255, 36) if dark else (38, 40, 42, 26)
    draw.rounded_rectangle((24, 22, width - 24, height - 22), radius=7, outline=frame, width=1)
    ink = (246, 243, 236, 255) if dark else (28, 31, 35, 255)
    draw.text((58, 54), "Xinchen Lee", font=font(58, True), fill=ink)
    subtitle_font = font(24)
    draw.text((60, 139), "AI, systems,", font=subtitle_font, fill=ink)
    draw.text((60, 171), "and things I felt like building.", font=subtitle_font, fill=ink)
    draw.line((60, 229, 456, 229), fill=secondary, width=1)

    # Three independent inputs enter a compact, unboxed routing region.  The
    # paths change order by a few pixels before they merge, avoiding a graph or
    # object-like motif while keeping the transformation legible.
    input_paths = [
        [(486, 100), (552, 100), (612, 118), (690, 112)],
        [(486, 150), (552, 150), (616, 146), (690, 150)],
        [(486, 200), (552, 200), (612, 180), (690, 184)],
    ]
    routing_paths = [
        [(690, 112), (720, 126), (742, 140), (760, 148)],
        [(690, 150), (724, 150), (760, 148)],
        [(690, 184), (718, 170), (740, 157), (760, 148)],
    ]
    main_path = [(760, 148), (794, 148), (824, 143), (856, 146)]
    breakaway = [(824, 143), (840, 170), (856, 190)]
    for path in input_paths + routing_paths:
        draw.line(path, fill=hairline, width=1, joint="curve")
    draw.line(main_path, fill=hairline, width=1, joint="curve")
    draw.line(breakaway, fill=secondary, width=1, joint="curve")

    # Pulse route follows one input through the transformation and along the
    # primary output. It is active for under half the cycle, leaving a quiet
    # interval at both ends so the loop has no visible reset.
    pulse_route = input_paths[1] + routing_paths[1][1:] + main_path[1:]
    active_start, active_end = 0.20, 0.68
    pulse_progress = (progress - active_start) / (active_end - active_start)
    pulse_alpha = smoothstep(active_start, active_start + 0.07, progress)
    pulse_alpha *= 1.0 - smoothstep(active_end - 0.07, active_end, progress)
    if pulse_alpha > 0.001:
        px, py, tx, ty = sample_polyline(pulse_route, pulse_progress)
        length = max(1.0, math.hypot(tx, ty))
        ux, uy = tx / length, ty / length
        pulse_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        pulse_draw = ImageDraw.Draw(pulse_layer, "RGBA")
        alpha = int(208 * pulse_alpha)
        pulse_draw.ellipse((px - 2.2, py - 2.2, px + 2.2, py + 2.2), fill=(*accent, alpha))
        pulse_draw.line(
            (px - ux * 5, py - uy * 5, px + ux * 5, py + uy * 5),
            fill=(*accent, max(32, alpha // 2)),
            width=1,
        )
        image = Image.alpha_composite(image.convert("RGBA"), pulse_layer).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")

    # The endpoint responds once as the pulse leaves the routing line. The
    # response is the same single accent and remains barely above the hairline.
    response = smoothstep(active_end - 0.15, active_end - 0.04, progress)
    response *= 1.0 - smoothstep(active_end - 0.015, active_end + 0.02, progress)
    if response > 0.001:
        rx, ry = breakaway[-1]
        draw.ellipse((rx - 2, ry - 2, rx + 2, ry + 2), fill=(*accent, int(96 * response)))
    return image.convert("RGB")


def hero_frame(index: int, total: int, dark: bool) -> Image.Image:
    return editorial_trace_frame(index, total, dark)


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


def sidequest_frame(index: int, total: int, dark: bool) -> Image.Image:
    """A compact footer echo, intentionally unlike the live signal strip."""
    width, height = 960, 150
    phase = math.tau * index / total
    image = field(width, height, phase, dark).filter(ImageFilter.GaussianBlur(13))
    veil = Image.new(
        "RGBA",
        image.size,
        (16, 18, 22, 210) if dark else (248, 246, 241, 211),
    )
    result = Image.alpha_composite(image.convert("RGBA"), veil)

    # Keep the mark at the footer's visual scale.  The canvas remains the
    # README-compatible size, but the asset is no longer a second full-width
    # instrument.
    anchor = (706, 94)
    node = (
        786 + 10 * math.sin(phase),
        88 + 5 * math.cos(2 * phase),
    )
    end = (846 + 7 * math.cos(phase), 70 + 8 * math.sin(phase))
    line = (234, 230, 221, 116) if dark else (55, 56, 57, 92)
    glow = (112, 216, 208, 220) if dark else (204, 96, 74, 175)
    soft_glow = Image.new("RGBA", result.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(soft_glow, "RGBA")
    sd.ellipse((node[0] - 46, node[1] - 46, node[0] + 46, node[1] + 46), fill=(*glow[:3], 24))
    soft_glow = soft_glow.filter(ImageFilter.GaussianBlur(18))
    result = Image.alpha_composite(result, soft_glow)

    draw = ImageDraw.Draw(result, "RGBA")
    draw.ellipse((anchor[0] - 3, anchor[1] - 3, anchor[0] + 3, anchor[1] + 3), fill=line)
    primary = bezier_points(
        anchor,
        (anchor[0] + 25, anchor[1] - 12 * math.cos(phase)),
        (node[0] - 30, node[1] + 12 * math.sin(phase)),
        node,
        samples=32,
    )
    draw.line(primary, fill=line, width=2, joint="curve")
    draw.line(primary[-13:], fill=glow, width=2, joint="curve")

    # Two short echo arcs breathe around the one departing node. Their small
    # radial pulse is the Side Quest grammar; it does not reuse Live's sweep.
    for arc_index, radius in enumerate((16, 26)):
        pulse = 1 + 0.16 * math.sin((arc_index + 1) * phase)
        arc_radius = radius * pulse
        arc_box = (
            node[0] - arc_radius,
            node[1] - arc_radius,
            node[0] + arc_radius,
            node[1] + arc_radius,
        )
        draw.arc(
            arc_box,
            start=198 - 4 * math.sin(phase),
            end=292 + 4 * math.cos(2 * phase),
            fill=(*glow[:3], 62 - arc_index * 17),
            width=2,
        )
    draw.ellipse((node[0] - 5, node[1] - 5, node[0] + 5, node[1] + 5), fill=glow)
    draw.ellipse(
        (node[0] - 9, node[1] - 9, node[0] + 9, node[1] + 9),
        outline=(*glow[:3], 64),
        width=1,
    )

    departure = bezier_points(
        node,
        (node[0] + 20, node[1] - 4 * math.sin(phase)),
        (end[0] - 26, end[1] + 10 * math.cos(phase)),
        end,
        samples=28,
    )
    draw.line(departure, fill=(*glow[:3], 78), width=2, joint="curve")
    draw.ellipse((end[0] - 2, end[1] - 2, end[0] + 2, end[1] + 2), fill=(*glow[:3], 112))
    return result.convert("RGB")


def save_animation(
    name: str,
    maker,
    dark: bool,
    frames_count: int,
    duration: int,
    optimize_gif: bool = True,
) -> None:
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
        optimize=optimize_gif,
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for dark in (False, True):
        save_animation(
            "hero",
            hero_frame,
            dark,
            HERO_FRAME_COUNT,
            HERO_FRAME_DURATION_MS,
            optimize_gif=False,
        )
        save_animation("live-signal", signal_frame, dark, 18, 190)
        save_animation("sidequest", sidequest_frame, dark, FRAME_COUNT, FRAME_DURATION_MS)
    print(f"Rendered motion and fallback assets to {ASSETS}")


if __name__ == "__main__":
    main()
