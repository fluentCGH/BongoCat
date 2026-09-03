#!/usr/bin/env python3
"""Render a lightweight GIF using the same transforms as the sprite runtime."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
MODEL = REPOSITORY / "src-tauri" / "assets" / "models" / "vessel"
OUTPUT = ROOT / "export" / "approved" / "vessel-action-preview.gif"
CANVAS = (1536, 1024)


def transform_layer(
    image: Image.Image,
    pivot: tuple[float, float],
    pressed: dict[str, object],
    amount: float,
) -> Image.Image:
    translate = pressed.get("Translate", [0, 0])
    scale = pressed.get("Scale", [1, 1])
    rotation = float(pressed.get("Rotation", 0)) * amount
    tx = float(translate[0]) * amount
    ty = float(translate[1]) * amount
    sx = 1 + (float(scale[0]) - 1) * amount
    sy = 1 + (float(scale[1]) - 1) * amount
    px, py = pivot
    cosine = math.cos(rotation)
    sine = math.sin(rotation)

    # Pillow expects an inverse affine mapping from destination to source.
    a = cosine / sx
    b = sine / sx
    d = -sine / sy
    e = cosine / sy
    c = px - a * (px + tx) - b * (py + ty)
    f = py - d * (px + tx) - e * (py + ty)

    return image.transform(
        CANVAS,
        Image.Transform.AFFINE,
        (a, b, c, d, e, f),
        resample=Image.Resampling.BICUBIC,
    )


def ease(value: float) -> float:
    return value * value * (3 - 2 * value)


def amounts() -> list[tuple[float, float]]:
    frames: list[tuple[float, float]] = [(0, 0)] * 8

    def tap(left: bool, right: bool) -> None:
        for index in range(6):
            value = ease((index + 1) / 6)
            frames.append((value if left else 0, value if right else 0))
        frames.extend([(1 if left else 0, 1 if right else 0)] * 4)
        for index in range(8):
            value = 1 - ease((index + 1) / 8)
            frames.append((value if left else 0, value if right else 0))
        frames.extend([(0, 0)] * 5)

    tap(left=True, right=False)
    tap(left=False, right=True)
    tap(left=True, right=True)
    return frames


def main() -> None:
    manifest = json.loads((MODEL / "vessel.sprite.json").read_text())
    layers = {item["Id"]: item for item in manifest["Layers"]}

    base = Image.open(MODEL / layers["base"]["File"]).convert("RGBA")
    left = Image.open(MODEL / layers["left-arm"]["File"]).convert("RGBA")
    right = Image.open(MODEL / layers["right-arm"]["File"]).convert("RGBA")
    foreground = Image.open(MODEL / layers["foreground"]["File"]).convert("RGBA")

    rendered: list[Image.Image] = []
    for left_amount, right_amount in amounts():
        frame = base.copy()
        frame.alpha_composite(
            transform_layer(
                left,
                tuple(layers["left-arm"]["Pivot"]),
                layers["left-arm"]["Pressed"],
                left_amount,
            )
        )
        frame.alpha_composite(
            transform_layer(
                right,
                tuple(layers["right-arm"]["Pivot"]),
                layers["right-arm"]["Pressed"],
                right_amount,
            )
        )
        frame.alpha_composite(foreground)

        preview = Image.new("RGB", CANVAS, "#f3f5f9")
        preview.paste(frame, mask=frame.getchannel("A"))
        preview.thumbnail((768, 512), Image.Resampling.LANCZOS)
        rendered.append(preview.quantize(colors=192, method=Image.Quantize.MEDIANCUT))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rendered[0].save(
        OUTPUT,
        save_all=True,
        append_images=rendered[1:],
        duration=40,
        loop=0,
        disposal=2,
        optimize=False,
    )


if __name__ == "__main__":
    main()
