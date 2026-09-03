#!/usr/bin/env python3
"""Build the approved Vessel artwork into BongoCat's sprite-model format.

The source artwork is intentionally kept as a single approved master.  This
script derives the two independently animated arms, a repaired background, and
an upper-body occluder without using any online background-removal service.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
SOURCE = ROOT / "source-art" / "vessel-bongocat-master.png"
OUTPUT = REPOSITORY / "src-tauri" / "assets" / "models" / "vessel"
CANVAS = (1536, 1024)

LEFT_KEYS = (
    "Alt AltGr BackQuote Backspace CapsLock Control ControlLeft ControlRight "
    "Delete Escape Fn KeyA KeyB KeyC KeyD KeyE KeyF KeyG KeyH KeyI KeyJ KeyK "
    "KeyL KeyM KeyN KeyO KeyP KeyQ KeyR KeyS KeyT KeyU KeyV KeyW KeyX KeyY "
    "KeyZ Meta Num0 Num1 Num2 Num3 Num4 Num5 Num6 Num7 Num8 Num9 Return Shift "
    "ShiftLeft ShiftRight Slash Space Tab"
).split()
RIGHT_KEYS = "DownArrow LeftArrow RightArrow UpArrow".split()


def supersampled_polygon(points: list[tuple[int, int]], scale: int = 4) -> Image.Image:
    """Create an antialiased polygon mask on the full model canvas."""
    mask = Image.new("L", (CANVAS[0] * scale, CANVAS[1] * scale), 0)
    scaled = [(x * scale, y * scale) for x, y in points]
    ImageDraw.Draw(mask).polygon(scaled, fill=255)
    return mask.resize(CANVAS, Image.Resampling.LANCZOS)


def arm_masks() -> tuple[Image.Image, Image.Image]:
    """Masks follow the approved v16 arm silhouettes.

    The root portions deliberately extend beneath the cloak.  A foreground
    layer later covers those hidden cuts, so rotations never expose a shoulder
    seam.
    """
    left_points = [
        (618, 689), (596, 706), (571, 728), (545, 753), (519, 778),
        (499, 795), (487, 808), (486, 819), (493, 829), (505, 835),
        (518, 834), (534, 824), (554, 807), (579, 784), (603, 759),
        (629, 737), (651, 723), (659, 704), (646, 691),
    ]
    right_points = [(CANVAS[0] - x, y) for x, y in left_points]
    return supersampled_polygon(left_points), supersampled_polygon(right_points)


def apply_mask(source: Image.Image, mask: Image.Image) -> Image.Image:
    alpha = np.asarray(
        ImageChops.multiply(source.getchannel("A"), mask),
        dtype=np.uint8,
    )
    pixels = np.asarray(source).copy()
    pixels[..., 3] = alpha
    pixels[alpha == 0, :3] = 0
    return Image.fromarray(pixels, mode="RGBA")


def nearest_fill(source: Image.Image, removal_mask: Image.Image) -> Image.Image:
    """Repair pixels hidden beneath arms using nearby visible artwork.

    Only a small area is ever revealed by the press animation.  Nearest-source
    filling preserves the local keyboard, mouse, cloak, and transparent-field
    colours without introducing a dependency on an online inpainting service.
    """
    rgba = np.asarray(source).copy()
    remove = np.asarray(removal_mask) > 8
    nearest = ndimage.distance_transform_edt(
        remove,
        return_distances=False,
        return_indices=True,
    )
    filled = rgba[tuple(nearest)]
    softened = np.empty_like(filled)
    for channel in range(4):
        softened[..., channel] = ndimage.gaussian_filter(
            filled[..., channel],
            sigma=5.0,
        )
    rgba[remove] = softened[remove]
    return Image.fromarray(rgba, mode="RGBA")


def foreground_mask(left_arm: Image.Image, right_arm: Image.Image) -> Image.Image:
    """Cover arm pivots with the approved head and cloak artwork."""
    mask = Image.new("L", CANVAS, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((500, 45, 1035, 650), fill=255)
    draw.polygon(
        [
            (568, 610), (968, 610), (1000, 710), (944, 791),
            (592, 791), (536, 710),
        ],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    arms = ImageChops.lighter(left_arm, right_arm)
    return ImageChops.subtract(mask, arms)


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def build_cover(source: Image.Image) -> None:
    cover = Image.new("RGBA", (612, 354), (0, 0, 0, 0))
    visible = source.crop(source.getchannel("A").getbbox())
    visible.thumbnail((588, 338), Image.Resampling.LANCZOS)
    x = (cover.width - visible.width) // 2
    y = (cover.height - visible.height) // 2
    cover.alpha_composite(visible, (x, y))
    save_png(cover, OUTPUT / "resources" / "cover.png")


def build_key_resources() -> None:
    """Key files opt the model into BongoCat's normal key routing.

    The hand movement is drawn by the sprite renderer, so the overlay itself is
    intentionally transparent.  Keeping the conventional filenames preserves
    the same supported-key behaviour as the bundled keyboard model.
    """
    marker = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    marker_path = OUTPUT / "resources" / "key-marker.png"
    save_png(marker, marker_path)

    for group, keys in (("left-keys", LEFT_KEYS), ("right-keys", RIGHT_KEYS)):
        directory = OUTPUT / "resources" / group
        directory.mkdir(parents=True, exist_ok=True)
        for key in keys:
            shutil.copyfile(marker_path, directory / f"{key}.png")

    marker_path.unlink()


def build_manifest() -> None:
    manifest = {
        "Version": 1,
        "Name": "Vessel",
        "Canvas": {"Width": CANVAS[0], "Height": CANVAS[1]},
        "Idle": {"Amplitude": 1.5, "Period": 3.2},
        "Layers": [
            {"Id": "base", "File": "layers/01_base.png"},
            {
                "Id": "left-arm",
                "File": "layers/02_left_arm.png",
                "Pivot": [626, 706],
                "Parameters": ["CatParamLeftHandDown"],
                "Pressed": {
                    "Translate": [0, 3],
                    "Rotation": -0.035,
                    "Scale": [1.0, 0.99],
                },
            },
            {
                "Id": "right-arm",
                "File": "layers/03_right_arm.png",
                "Pivot": [910, 706],
                "Parameters": [
                    "CatParamRightHandDown",
                    "ParamMouseLeftDown",
                    "ParamMouseRightDown",
                ],
                "Pressed": {
                    "Translate": [0, 3],
                    "Rotation": 0.035,
                    "Scale": [1.0, 0.99],
                },
            },
            {"Id": "foreground", "File": "layers/04_foreground.png"},
        ],
    }
    path = OUTPUT / "vessel.sprite.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    if source.size != CANVAS:
        raise ValueError(f"expected {CANVAS}, got {source.size}")

    left_mask, right_mask = arm_masks()
    removal = ImageChops.lighter(left_mask, right_mask).filter(ImageFilter.MaxFilter(9))

    base = nearest_fill(source, removal)
    left_arm = apply_mask(source, left_mask)
    right_arm = apply_mask(source, right_mask)
    foreground = apply_mask(source, foreground_mask(left_mask, right_mask))

    save_png(base, OUTPUT / "layers" / "01_base.png")
    save_png(left_arm, OUTPUT / "layers" / "02_left_arm.png")
    save_png(right_arm, OUTPUT / "layers" / "03_right_arm.png")
    save_png(foreground, OUTPUT / "layers" / "04_foreground.png")
    build_cover(source)
    build_key_resources()
    build_manifest()


if __name__ == "__main__":
    main()
