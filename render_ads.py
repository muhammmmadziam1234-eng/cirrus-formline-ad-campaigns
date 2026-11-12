"""Compose the Cirrus and Formline product advertisements from the studio renders."""

import argparse
import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps


HERE = Path(__file__).resolve().parent
WIDTH = 1080
SCALE = 2
RESAMPLE = Image.Resampling.LANCZOS
WINDOWS_FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
FONTS = {
    "sans": ("bahnschrift.ttf", "arial.ttf", "DejaVuSans.ttf"),
    "bold": ("seguisb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "mono": ("consola.ttf", "DejaVuSansMono.ttf"),
    "serif": ("BOD_R.TTF", "times.ttf", "DejaVuSerif.ttf"),
}

CIRRUS = {
    "paper": "#e9f0e9",
    "ink": "#142b2a",
    "muted": "#3f5955",
    "rule": "#91a7a0",
    "jade": "#b4d8bf",
    "dark": "#192a2f",
    "light": "#e9f0e9",
}

FORMLINE = {
    "paper": "#f0e4d5",
    "dark": "#201d1c",
    "ink": "#261f1b",
    "light": "#f8eee3",
    "muted": "#4e3c33",
    "accent": "#c44821",
    "copper": "#fa8a59",
}


@lru_cache
def typeface(role, size):
    for name in FONTS[role]:
        for candidate in (str(WINDOWS_FONTS / name), name):
            try:
                return ImageFont.truetype(candidate, size * SCALE)
            except OSError:
                continue
    return ImageFont.load_default(size=size * SCALE)


class Layout:
    """Lay out at double resolution and export with antialiased type and rules."""

    def __init__(self, height, ground):
        self.height = height
        self.image = Image.new("RGB", (WIDTH * SCALE, height * SCALE), ground)
        self.draw = ImageDraw.Draw(self.image)

    def line(self, points, fill, width=1):
        self.draw.line(
            [(round(x * SCALE), round(y * SCALE)) for x, y in points],
            fill=fill,
            width=width * SCALE,
            joint="curve",
        )

    def rect(self, x, y, width, height, fill):
        self.draw.rectangle(
            (x * SCALE, y * SCALE, (x + width) * SCALE - 1, (y + height) * SCALE - 1),
            fill=fill,
        )

    def circle(self, x, y, radius, fill):
        self.draw.ellipse(
            ((x-radius)*SCALE, (y-radius)*SCALE, (x+radius)*SCALE, (y+radius)*SCALE),
            fill=fill,
        )

    def text(self, x, y, value, role, size, fill, *, tracking=0, align="left"):
        font = typeface(role, size)
        baseline = y * SCALE
        start = x * SCALE
        gap = tracking * SCALE
        width = font.getlength(value) + max(len(value) - 1, 0) * gap
        if align == "right":
            start -= width
        left, top, right, bottom = font.getbbox(value, anchor="ls")
        if start + min(left, 0) < 0 or start + max(width, right) > WIDTH * SCALE:
            raise ValueError(f"Text exceeds the canvas width: {value!r}")
        if baseline + top < 0 or baseline + bottom > self.height * SCALE:
            raise ValueError(f"Text exceeds the canvas height: {value!r}")
        if not tracking:
            self.draw.text((start, baseline), value, font=font, fill=fill, anchor="ls")
            return
        for index, char in enumerate(value):
            prefix = value[:index + 1]
            position = start + font.getlength(prefix) - font.getlength(char) + index * gap
            self.draw.text((position, baseline), char, font=font, fill=fill, anchor="ls")

    def photo(self, image, box, *, focus=(0.5, 0.5)):
        """Use a crop only to fill the frame, without changing the source render."""
        x, y, width, height = box
        if min(x, y) < 0 or x + width > WIDTH or y + height > self.height:
            raise ValueError(f"Photo exceeds the canvas: {box!r}")
        fitted = ImageOps.fit(
            image, (width*SCALE, height*SCALE), method=RESAMPLE, centering=focus
        )
        self.image.paste(fitted, (x*SCALE, y*SCALE))

    def finish(self):
        return self.image.resize((WIDTH, self.height), RESAMPLE)


def cirrus_mark(page):
    c = CIRRUS
    for offset in (0, 8, 16):
        page.line(
            [(53, 52+offset), (69, 52+offset), (76, 47+offset), (89, 47+offset)],
            c["ink"],
            3,
        )
    page.text(105, 74, "Cirrus", "bold", 38, c["ink"], tracking=-1.1)
    page.text(1028, 71, "ENVIRONMENTAL SENSOR  /  C-01", "mono", 18, c["muted"], align="right")
    page.line([(52, 101), (1028, 101)], c["rule"])


def cirrus_square(hero):
    c = CIRRUS
    page = Layout(1080, c["paper"])
    cirrus_mark(page)
    page.rect(418, 201, 610, 610, c["jade"])
    page.photo(hero, (397, 180, 610, 610))

    page.text(52, 243, "INDOOR AIR", "mono", 18, c["muted"], tracking=1.6)
    page.text(47, 368, "Air", "bold", 122, c["ink"], tracking=-5)
    page.text(46, 473, "in view.", "bold", 88, c["ink"], tracking=-4)
    for y, text in (
        (553, "A wall-mounted sensor"),
        (591, "with a vented face and"),
        (629, "a visible status light."),
    ):
        page.text(52, y, text, "sans", 26, c["muted"])
    page.circle(59, 714, 6, "#4d8068")
    page.line([(77, 714), (160, 714)], c["rule"])

    page.rect(0, 865, 1080, 215, c["jade"])
    page.text(52, 925, "A closer look at the enclosure", "bold", 28, c["ink"])
    page.line([(52, 949), (1028, 949)], "#7a9c87")
    for x, text in ((52, "Vented front"), (383, "Status indicator"), (713, "Wall cleat")):
        page.text(x, 1010, text, "sans", 26, c["ink"])
    return page.finish()


def cirrus_vertical(hero, exploded):
    c = CIRRUS
    page = Layout(1350, c["paper"])
    cirrus_mark(page)
    page.text(47, 244, "Air in view.", "bold", 132, c["ink"], tracking=-5.4)

    page.rect(72, 311, 575, 575, c["jade"])
    page.photo(hero, (52, 291, 575, 575))
    page.text(691, 352, "A wall-mounted sensor", "bold", 28, c["ink"])
    page.text(691, 391, "for indoor air.", "sans", 27, c["muted"])
    for y, title, detail in (
        (472, "Vented face", "Air intake at the front"),
        (615, "Status light", "Visible on the enclosure"),
        (758, "Wall cleat", "A separate mounting plate"),
    ):
        page.line([(691, y), (1028, y)], c["rule"])
        page.text(691, y+53, title, "bold", 29, c["ink"])
        page.text(691, y+90, detail, "sans", 24, c["muted"])

    page.rect(0, 924, 1080, 426, c["dark"])
    page.text(52, 998, "EXPLODED ASSEMBLY", "mono", 18, "#b4d8bf", tracking=1)
    page.text(52, 1092, "Inside", "bold", 70, c["light"], tracking=-2)
    page.text(52, 1170, "Cirrus.", "bold", 70, c["light"], tracking=-2)
    page.text(54, 1258, "Housing, gasket, and board", "sans", 24, c["light"])
    page.photo(exploded, (406, 945, 622, 395))
    return page.finish()


def formline_mark(page):
    f = FORMLINE
    page.line([(53, 73), (68, 51), (90, 51)], f["copper"], 4)
    page.rect(86, 47, 14, 8, f["copper"])
    page.text(114, 75, "Formline", "bold", 35, f["light"], tracking=-0.9)
    page.text(1028, 71, "ARTICULATED DESK LAMP", "mono", 18, f["light"], align="right")


def formline_square(hero):
    f = FORMLINE
    page = Layout(1080, f["dark"])
    page.photo(hero, (0, 0, 1080, 890))
    formline_mark(page)
    page.rect(0, 881, 1080, 199, f["paper"])
    page.rect(52, 921, 32, 4, f["accent"])
    page.text(48, 1002, "Light follows your lead.", "serif", 82, f["ink"], tracking=-1.5)
    page.text(52, 1044, "Adjust the arm and tilt the head to place the light.", "sans", 25, f["muted"])
    return page.finish()


def formline_vertical(hero, detail):
    f = FORMLINE
    page = Layout(1350, f["dark"])
    formline_mark(page)
    page.line([(52, 102), (1028, 102)], "#645147")
    page.text(48, 222, "Light follows your lead.", "serif", 94, f["light"], tracking=-1.7)
    page.photo(hero, (52, 264, 976, 804))

    page.rect(0, 1068, 1080, 282, f["paper"])
    page.rect(52, 1110, 33, 4, f["accent"])
    page.text(52, 1163, "A closer look", "serif", 49, f["ink"], tracking=-0.5)
    page.text(53, 1220, "Twin arms and a pivoting head", "sans", 26, f["muted"])
    page.text(53, 1255, "let you reposition the light.", "sans", 26, f["muted"])
    page.photo(detail, (669, 1087, 359, 244), focus=(0.42, 0.72))
    return page.finish()


def read_render(folder, filename):
    paths = (folder / filename, folder / "renders" / filename)
    for path in paths:
        if path.is_file():
            with Image.open(path) as image:
                return ImageOps.exif_transpose(image).convert("RGB")
    raise FileNotFoundError(f"Missing Blender render: {paths[0]} or {paths[1]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", choices=("all", "cirrus", "formline"), default="all")
    parser.add_argument("--cirrus-dir", type=Path, default=HERE / "assets" / "cirrus")
    parser.add_argument("--formline-dir", type=Path, default=HERE / "assets" / "formline")
    parser.add_argument("--output-dir", type=Path, default=HERE / "exports")
    args = parser.parse_args()

    layouts = {}
    try:
        if args.campaign in ("all", "cirrus"):
            hero = read_render(args.cirrus_dir, "hero.png")
            exploded = read_render(args.cirrus_dir, "exploded.png")
            layouts["cirrus-square"] = cirrus_square(hero)
            layouts["cirrus-vertical"] = cirrus_vertical(hero, exploded)
        if args.campaign in ("all", "formline"):
            hero = read_render(args.formline_dir, "hero.png")
            detail = read_render(args.formline_dir, "detail.png")
            layouts["formline-square"] = formline_square(hero)
            layouts["formline-vertical"] = formline_vertical(hero, detail)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    for name, image in layouts.items():
        target = args.output_dir / f"{name}.png"
        image.save(target, optimize=True, icc_profile=srgb)
        print(f"{target.name} | {image.width} x {image.height}")


if __name__ == "__main__":
    main()
