#!/usr/bin/env python3
"""Validate the generated Vessel sprite package and its rest-pose fidelity."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
MODEL = REPOSITORY / "src-tauri" / "assets" / "models" / "vessel"
MASTER = ROOT / "source-art" / "vessel-bongocat-master.png"
MANIFEST = MODEL / "vessel.sprite.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    data = json.loads(MANIFEST.read_text())
    require(data["Version"] == 1, "unsupported sprite manifest version")

    canvas = (data["Canvas"]["Width"], data["Canvas"]["Height"])
    require(canvas == (1536, 1024), f"unexpected canvas: {canvas}")

    composite = Image.new("RGBA", canvas, (0, 0, 0, 0))
    parameter_names: set[str] = set()

    for layer in data["Layers"]:
        path = MODEL / layer["File"]
        require(path.is_file(), f"missing layer: {path}")
        image = Image.open(path).convert("RGBA")
        require(image.size == canvas, f"wrong layer size: {path}")
        require(image.getchannel("A").getbbox() is not None, f"empty layer: {path}")
        composite.alpha_composite(image)
        parameter_names.update(layer.get("Parameters", []))

    required_parameters = {
        "CatParamLeftHandDown",
        "CatParamRightHandDown",
        "ParamMouseLeftDown",
        "ParamMouseRightDown",
    }
    require(
        required_parameters <= parameter_names,
        f"missing parameters: {sorted(required_parameters - parameter_names)}",
    )

    left_keys = list((MODEL / "resources" / "left-keys").glob("*.png"))
    right_keys = list((MODEL / "resources" / "right-keys").glob("*.png"))
    require(len(left_keys) >= 50, "left keyboard key map is incomplete")
    require(len(right_keys) >= 4, "right keyboard key map is incomplete")

    cover = Image.open(MODEL / "resources" / "cover.png")
    require(cover.size == (612, 354), "cover must match the preset-card ratio")

    expected = np.asarray(Image.open(MASTER).convert("RGBA"), dtype=np.int16)
    actual = np.asarray(composite, dtype=np.int16)
    difference = np.abs(expected - actual)
    changed_ratio = float(np.mean(np.any(difference > 8, axis=2)))
    require(
        changed_ratio < 0.01,
        f"rest-pose reconstruction drifted: {changed_ratio:.2%} pixels changed",
    )

    print(
        "Vessel sprite model OK: "
        f"{len(data['Layers'])} layers, "
        f"{len(left_keys) + len(right_keys)} key mappings, "
        f"{changed_ratio:.3%} rest-pose pixel drift"
    )


if __name__ == "__main__":
    main()
