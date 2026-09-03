# Vessel BongoCat model

This directory contains the reproducible source pipeline for the Vessel model.
The approved design is `source-art/vessel-bongocat-concept-v16-chroma.png`.
Later concept iterations are intentionally excluded from the build.

## Build pipeline

Run these commands from the repository root:

```bash
python3 custom-models/vessel-live2d/scripts/remove_chroma.py \
  custom-models/vessel-live2d/source-art/vessel-bongocat-concept-v16-chroma.png \
  custom-models/vessel-live2d/source-art/vessel-bongocat-master.png

python3 custom-models/vessel-live2d/scripts/build_sprite_model.py
python3 custom-models/vessel-live2d/scripts/validate_sprite_model.py
```

The generated, application-ready model is written to
`src-tauri/assets/models/vessel/`.

## Runtime format

The upstream application normally loads Cubism `.moc3` models. Cubism's model
compiler is proprietary, so this fork also accepts a layered `.sprite.json`
model. Existing `.model3.json` models continue to use the original Live2D
loader without any change.

The Vessel package contains four aligned 1536 x 1024 transparent layers:

1. repaired static base;
2. left arm;
3. right arm;
4. head-and-cloak foreground occluder.

The standard BongoCat parameter names are retained:

- `CatParamLeftHandDown`: left-side keyboard input;
- `CatParamRightHandDown`: right-side keyboard input;
- `ParamMouseLeftDown` and `ParamMouseRightDown`: mouse input.

Only a subtle arm press and smooth return are enabled for the first version.
Expressions and additional motions can be added to the same manifest later.

## Artwork note

This is an unofficial fan-made character model inspired by _Hollow Knight_.
Check the applicable IP and distribution requirements before publishing or
commercialising a packaged build.
