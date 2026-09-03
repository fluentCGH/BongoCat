#!/usr/bin/env python3
"""Convert a bright-green ImageGen background into a real alpha channel.

The threshold is based on green dominance rather than a single RGB value so it
also handles the slightly graded green produced around antialiased outlines.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def remove_green(input_path: Path, output_path: Path) -> None:
    """Remove the graded chroma field while retaining antialiased edges.

    Pixels whose green channel dominates by 160 or more are background, while
    pixels below 40 are fully foreground. Values between those thresholds form
    a smooth edge matte.
    """
    source = Image.open(input_path).convert("RGBA")
    cleaned = Image.new("RGBA", source.size)
    source_pixels = source.load()
    cleaned_pixels = cleaned.load()

    for y in range(source.height):
        for x in range(source.width):
            red, green, blue, alpha = source_pixels[x, y]
            green_dominance = max(0, green - max(red, blue))

            foreground_alpha = clamp((160.0 - green_dominance) / 120.0)

            next_alpha = round(alpha * foreground_alpha)

            if next_alpha == 0:
                red = green = blue = 0
            elif next_alpha < 255:
                # The model palette contains no green; neutralising it avoids
                # a visible halo on both light and dark desktop backgrounds.
                green = min(green, max(red, blue))

            cleaned_pixels[x, y] = red, green, blue, next_alpha

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(output_path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    remove_green(args.input, args.output)


if __name__ == "__main__":
    main()
