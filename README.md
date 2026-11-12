# Cirrus and Formline product campaigns

Two original fictional product campaigns built around editable Blender models. Each campaign has a square 1080 × 1080 placement and a portrait 1080 × 1350 placement with its own composition.

<img src="exports/cirrus-square.png" alt="Cirrus square advertisement" width="420"> <img src="exports/formline-square.png" alt="Formline square advertisement" width="420">

## Cirrus

**Read the air.** A cool palette frames the environmental sensor. The portrait places the enclosure and an exploded view together so the reader can see the assembly behind the silhouette.

[Square placement](exports/cirrus-square.png) · [Portrait placement](exports/cirrus-vertical.png) · [Blender project](https://github.com/muhammmmadziam1234-eng/cirrus-environment-sensor)

## Formline

**Put light in its place.** A warm palette and a serif headline frame the articulated desk lamp. The portrait pairs the full lamp with a close view of a joint.

[Square placement](exports/formline-square.png) · [Portrait placement](exports/formline-vertical.png) · [Blender project](https://github.com/muhammmmadziam1234-eng/formline-articulated-lamp)

## Editable source and export

[render_ads.py](render_ads.py) contains the layout, text, colors and crop settings. The source renders are included in [assets](assets). The exporter uses Pillow and locally installed fonts with system font fallbacks.

~~~sh
python -m pip install -r requirements.txt
python render_ads.py
~~~

Use `--campaign cirrus` or `--campaign formline` to export one family. `--cirrus-dir` and `--formline-dir` accept alternate render folders. The default output is `exports`, where the four sRGB PNGs are saved.
