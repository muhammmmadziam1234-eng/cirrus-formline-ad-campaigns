"""Compose two seven-second, 9:16 campaign edits from the existing Blender renders."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from imageio_ffmpeg import read_frames, write_frames
from PIL import Image, ImageCms, ImageOps

from render_ads import CIRRUS, FORMLINE, HERE, Layout, RESAMPLE, read_render


SIZE = (1080, 1920)
FPS = 24
SCENE_LENGTHS = (48, 60, 60)
PORTRAIT = (84, 602, 840, 840)
DETAIL = (84, 724, 840, 540)
END_FRAME = (84, 626, 840, 764)
ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


@dataclass(frozen=True)
class Beat:
    headline: tuple[str, ...]
    caption: tuple[str, ...]
    render: str
    box: tuple[int, int, int, int]
    focus: tuple[float, float] = (0.5, 0.5)


STORIES = {
    "cirrus": (
        Beat(("Air in view.",), ("A wall-mounted environmental sensor.",), "hero", PORTRAIT),
        Beat(("Look inside.",), ("Vented face. Separate sensing bay.", "Removable wall cleat."), "exploded", DETAIL),
        Beat(("Cirrus C-01",), ("Environmental sensor design.",), "hero", END_FRAME),
    ),
    "formline": (
        Beat(("Light follows", "your lead."), ("An articulated desk lamp.",), "hero", PORTRAIT),
        Beat(("Find your angle.",), ("Twin links and an adjustable head.",), "detail", DETAIL, (0.48, 0.63)),
        Beat(("Formline",), ("Articulated desk lamp design.",), "hero", END_FRAME),
    ),
}


def build_card(name, beat):
    is_cirrus = name == "cirrus"
    if is_cirrus:
        ground, ink, accent, soft = CIRRUS["paper"], CIRRUS["ink"], "#436e5b", CIRRUS["muted"]
        label, type_style = "CIRRUS / C-01", "bold"
    else:
        ground, ink, accent, soft = FORMLINE["dark"], FORMLINE["light"], FORMLINE["copper"], "#d9c5b8"
        label, type_style = "FORMLINE", "serif"
    card = Layout(SIZE[1], ground)
    card.rect(84, 249, 29, 5, accent)
    card.text(133, 269, label, "mono", 26, soft, tracking=2.1)
    for index, line in enumerate(beat.headline):
        card.text(79, 435 + index * 105, line, type_style, 98, ink, tracking=-2.9)

    x, y, w, h = beat.box
    card.line([(x, y - 16), (x + w, y - 16)], accent, width=2)
    card.line([(84, 1477), (924, 1477)], accent, width=2)
    for index, line in enumerate(beat.caption):
        card.text(84, 1535 + index * 42, line, "sans", 31, soft)
    return card.finish()


def frame_at(card, photo, beat, phase):
    x, y, width, height = beat.box
    # Ease a small camera push in the crop while type stays fixed on screen.
    eased = phase * phase * (3.0 - 2.0 * phase)
    zoom = 1.0 + eased * 0.045
    crop = ImageOps.fit(
        photo,
        (round(width * zoom), round(height * zoom)),
        method=RESAMPLE,
        centering=beat.focus,
    )
    left = round((crop.width - width) * beat.focus[0])
    top = round((crop.height - height) * beat.focus[1])
    frame = card.copy()
    frame.paste(crop.crop((left, top, left + width, top + height)), (x, y))
    return frame


def verify_video(path):
    reader = read_frames(str(path))
    try:
        metadata = next(reader)
        frames = sum(1 for _ in reader)
    finally:
        reader.close()
    if (
        metadata["size"] != SIZE
        or round(metadata["fps"], 3) != FPS
        or frames != sum(SCENE_LENGTHS)
        or metadata["codec"] != "h264"
    ):
        raise ValueError(f"Unexpected video export: {metadata}; decoded {frames} frames")
    return frames


def export_campaign(name, output_dir):
    target = output_dir / f"{name}-story.mp4"
    folder = HERE / "assets" / name
    beats = STORIES[name]
    renders = {key: read_render(folder, f"{key}.png") for key in {beat.render for beat in beats}}
    storyboard = Image.new("RGB", (882, 480), "#262b2a")
    writer = write_frames(
        str(target), SIZE, fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-movflags", "+faststart",
                       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"],
    )
    writer.send(None)
    try:
        for index, (beat, count) in enumerate(zip(beats, SCENE_LENGTHS, strict=True)):
            card = build_card(name, beat)
            for step in range(count):
                frame = frame_at(card, renders[beat.render], beat, step / (count - 1))
                if step == count // 2:
                    storyboard.paste(frame.resize((270, 480), RESAMPLE), (index * 306, 0))
                if index == 0 and step == count // 2:
                    frame.save(output_dir / f"{name}-story-poster.png", optimize=True, icc_profile=ICC)
                writer.send(frame.tobytes())
    finally:
        writer.close()
    frames = verify_video(target)
    storyboard.save(output_dir / f"{name}-storyboard.png", optimize=True, icc_profile=ICC)
    print(f"{target.name} | {SIZE[0]} × {SIZE[1]} | {FPS} fps | {frames} decoded frames")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", choices=("all", *STORIES), default="all")
    parser.add_argument("--output-dir", type=Path, default=HERE / "exports")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for campaign in STORIES if args.campaign == "all" else (args.campaign,):
        export_campaign(campaign, args.output_dir)


if __name__ == "__main__":
    main()
