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

## Windows installer

Run the `Build Vessel for Windows` workflow manually in GitHub Actions. It
validates the committed model, type-checks the frontend, builds the Tauri NSIS
bundle, and uploads the unsigned x64 installer as the
`vessel-bongocat-windows-x64` artifact.

## Runtime format

The upstream application normally loads Cubism `.moc3` models. Cubism's model
compiler is proprietary, so this fork also accepts a layered `.sprite.json`
model. Existing `.model3.json` models continue to use the original Live2D
loader without any change.

The Vessel package contains six aligned 1536 x 1024 transparent layers:

1. repaired static base;
2. left arm;
3. right arm;
4. head-and-cloak foreground occluder;
5. left eye;
6. right eye.

The standard BongoCat parameter names are retained:

- `CatParamLeftHandDown`: left-side keyboard input;
- `CatParamRightHandDown`: right-side keyboard input;
- `ParamMouseLeftDown` and `ParamMouseRightDown`: mouse input.

The current action set uses a snappy press with a softer return plus a subtle,
randomised synchronized blink. The approved rest pose remains unchanged.
Expressions and additional motions can be added to the same manifest later.

## Artwork note

This is an unofficial fan-made character model inspired by _Hollow Knight_.
Check the applicable IP and distribution requirements before publishing or
commercialising a packaged build.
