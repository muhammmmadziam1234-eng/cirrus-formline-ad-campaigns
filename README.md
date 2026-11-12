# Cirrus and Formline product campaigns

Product advertising and art direction for two industrial design projects. Each campaign uses original Blender renders in a 1080 × 1080 square placement and a separately composed 1080 × 1350 portrait placement.

<img src="exports/cirrus-square.png" alt="Cirrus square advertisement" width="420"> <img src="exports/formline-square.png" alt="Formline square advertisement" width="420">

## Cirrus

**Air in view.** A pale green layout frames the complete wall-mounted sensor. The portrait pairs its front face and mounting details with a full exploded assembly.

[Square placement](exports/cirrus-square.png) · [Portrait placement](exports/cirrus-vertical.png) · [Blender project](https://github.com/muhammmmadziam1234-eng/cirrus-environment-sensor)

## Formline

**Light follows your lead.** Warm studio lighting shows the full lamp silhouette. The portrait places a joint close-up below the complete product to show how the lamp articulates.

[Square placement](exports/formline-square.png) · [Portrait placement](exports/formline-vertical.png) · [Blender project](https://github.com/muhammmmadziam1234-eng/formline-articulated-lamp)

## Editable source and export

[render_ads.py](render_ads.py) contains the layout, text, colors and crop settings. The source renders are included in [assets](assets). The exporter uses Pillow and locally installed fonts with system font fallbacks.

~~~sh
python -m pip install -r requirements.txt
python render_ads.py
~~~

Use `--campaign cirrus` or `--campaign formline` to export one family. `--cirrus-dir` and `--formline-dir` accept alternate render folders. The default output is `exports`, where the four sRGB PNGs are saved.
