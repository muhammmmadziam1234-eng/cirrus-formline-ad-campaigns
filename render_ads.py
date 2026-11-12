"""Editable art direction and PNG exporter for the Cirrus and Formline concepts."""

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
    "cirrus": ("bahnschrift.ttf", "arial.ttf", "DejaVuSans.ttf"),
    "cirrus-bold": ("GOTHICB.TTF", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "formline": ("BOD_R.TTF", "times.ttf", "DejaVuSerif.ttf"),
    "formline-bold": ("corbelb.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "formline-text": ("corbel.ttf", "arial.ttf", "DejaVuSans.ttf"),
}

CIRRUS = {
    "ground": "#0b1820",
    "mat": "#12252d",
    "type": "#ecf6f3",
    "muted": "#adc3c6",
    "accent": "#9ae9ce",
    "rule": "#37535a",
}
FORMLINE = {
    "paper": "#f3f1ed",
    "mat": "#242421",
    "ink": "#201e1b",
    "muted": "#514941",
    "accent": "#bf361f",
    "rule": "#beb5a9",
}

# Crops are normalized source coordinates (left, top, right, bottom).
# Each focal point is Pillow's alignment within the remaining crop range.
PHOTOS = {
    "cirrus-square-hero": {"focus": (0.50, 0.48)},
    "cirrus-vertical-hero": {"focus": (0.50, 0.49)},
    "cirrus-vertical-exploded": {"focus": (0.50, 0.50)},
    "formline-square-hero": {"focus": (0.50, 0.50)},
    "formline-vertical-hero": {"focus": (0.50, 0.50)},
    "formline-vertical-detail": {"focus": (0.50, 0.50)},
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
    """Pixel-based page with baseline typography and supersampled artwork."""

    def __init__(self, height, ground):
        self.image = Image.new("RGB", (WIDTH * SCALE, height * SCALE), ground)
        self.draw = ImageDraw.Draw(self.image)

    def line(self, points, fill, width=1):
        self.draw.line(
            [(round(x * SCALE), round(y * SCALE)) for x, y in points],
            fill=fill,
            width=width * SCALE,
            joint="curve",
        )

    def rect(self, x, y, w, h, fill):
        self.draw.rectangle(
            (x * SCALE, y * SCALE, (x + w) * SCALE - 1, (y + h) * SCALE - 1),
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
        if start < 0 or start + width > WIDTH * SCALE:
            raise ValueError(f"Text exceeds the canvas: {value!r}")
        if not tracking:
            self.draw.text((start, baseline), value, font=font, fill=fill, anchor="ls")
            return
        for index, char in enumerate(value):
            prefix = value[: index + 1]
            position = start + font.getlength(prefix) - font.getlength(char) + index * gap
            self.draw.text((position, baseline), char, font=font, fill=fill, anchor="ls")

    def photo(self, image, box, treatment, mat):
        x, y, w, h = box
        settings = PHOTOS[treatment]
        if "crop" in settings:
            left, top, right, bottom = settings["crop"]
            image = image.crop(
                (
                    round(left * image.width),
                    round(top * image.height),
                    round(right * image.width),
                    round(bottom * image.height),
                )
            )
        size = (w * SCALE, h * SCALE)
        if settings.get("fit") == "contain":
            fitted = ImageOps.contain(image, size, method=RESAMPLE)
            center_x, center_y = settings["focus"]
            left = round((size[0] - fitted.width) * center_x)
            top = round((size[1] - fitted.height) * center_y)
        else:
            fitted = ImageOps.fit(image, size, method=RESAMPLE, centering=settings["focus"])
            left = top = 0
        plate = Image.new("RGBA", size, mat)
        plate.alpha_composite(fitted, (left, top))
        self.image.paste(plate.convert("RGB"), (x * SCALE, y * SCALE))

    def finish(self):
        return self.image.resize(
            (self.image.width // SCALE, self.image.height // SCALE), RESAMPLE
        )


def cirrus_wordmark(page):
    accent = CIRRUS["accent"]
    page.line([(59, 50), (75, 50), (81, 45), (96, 45)], accent, 3)
    page.line([(59, 58), (81, 58), (87, 53), (96, 53)], accent, 3)
    page.line([(59, 66), (87, 66), (93, 61), (96, 61)], accent, 3)
    page.text(111, 69, "Cirrus", "cirrus-bold", 37, CIRRUS["type"], tracking=-0.8)
    page.text(
        1022, 65, "Indoor environmental sensor", "cirrus", 23,
        CIRRUS["muted"], align="right"
    )
    page.line([(58, 95), (1022, 95)], CIRRUS["rule"])


def cirrus_square(hero):
    c = CIRRUS
    page = Layout(1080, c["ground"])
    cirrus_wordmark(page)
    page.text(53, 238, "Read the air.", "cirrus", 126, c["type"], tracking=-4)
    page.photo(hero, (58, 278, 964, 591), "cirrus-square-hero", c["mat"])
    page.line([(58, 923), (1022, 923)], c["rule"])
    page.rect(58, 957, 4, 65, c["accent"])
    page.text(80, 982, "Get to know the air", "cirrus", 30, c["type"])
    page.text(80, 1018, "in the spaces you use every day.", "cirrus", 30, c["type"])
    return page.finish()


def cirrus_vertical(hero, exploded):
    c = CIRRUS
    page = Layout(1350, c["ground"])
    cirrus_wordmark(page)
    page.text(53, 234, "Read the air.", "cirrus", 126, c["type"], tracking=-4)
    page.text(59, 283, "Get to know the air indoors.", "cirrus", 29, c["muted"])
    page.photo(hero, (58, 323, 964, 616), "cirrus-vertical-hero", c["mat"])
    page.line([(58, 975), (1022, 975)], c["rule"])
    page.rect(58, 1018, 4, 31, c["accent"])
    page.text(75, 1044, "Inside Cirrus", "cirrus", 37, c["type"], tracking=-0.5)
    page.text(58, 1091, "A closer look at the sensor", "cirrus", 24, c["muted"])
    page.text(58, 1122, "and its enclosure.", "cirrus", 24, c["muted"])
    page.photo(exploded, (440, 1002, 582, 277), "cirrus-vertical-exploded", c["mat"])
    page.line([(58, 1300), (1022, 1300)], c["rule"])
    return page.finish()


def formline_wordmark(page):
    f = FORMLINE
    page.line([(57, 71), (73, 45), (97, 45)], f["accent"], 4)
    page.rect(94, 41, 15, 8, f["accent"])
    page.text(123, 68, "Formline", "formline-bold", 40, f["ink"], tracking=-1.3)


def formline_square(hero):
    f = FORMLINE
    page = Layout(1080, f["paper"])
    page.photo(hero, (447, 0, 633, 1080), "formline-square-hero", f["mat"])
    formline_wordmark(page)
    page.line([(57, 106), (403, 106)], f["rule"])
    for y, value in ((321, "Put light"), (424, "in its"), (527, "place.")):
        page.text(51, y, value, "formline", 99, f["ink"], tracking=-2)
    page.rect(57, 917, 37, 4, f["accent"])
    page.text(57, 974, "Articulated desk lamp", "formline-bold", 25, f["ink"])
    page.text(57, 1014, "Angle the light for the task.", "formline-text", 26, f["muted"])
    return page.finish()


def formline_vertical(hero, detail):
    f = FORMLINE
    page = Layout(1350, f["paper"])
    page.photo(hero, (256, 349, 824, 1001), "formline-vertical-hero", f["mat"])
    formline_wordmark(page)
    page.text(
        1022, 65, "Articulated desk lamp", "formline-bold", 25, f["ink"], align="right"
    )
    page.line([(57, 102), (1022, 102)], f["rule"])
    page.text(50, 221, "Put light in", "formline", 110, f["ink"], tracking=-2.4)
    page.text(51, 319, "its place.", "formline", 110, f["ink"], tracking=-2.4)
    page.rect(57, 400, 35, 4, f["accent"])
    page.text(57, 454, "Angle the light", "formline-text", 25, f["muted"])
    page.text(57, 483, "for the task.", "formline-text", 25, f["muted"])
    page.rect(50, 933, 306, 247, f["paper"])
    page.photo(detail, (57, 940, 292, 233), "formline-vertical-detail", f["mat"])
    page.text(57, 1211, "Hinge detail", "formline-bold", 22, f["ink"])
    return page.finish()


def read_render(folder, filename):
    paths = (folder / filename, folder / "renders" / filename)
    for path in paths:
        if path.is_file():
            with Image.open(path) as image:
                return ImageOps.exif_transpose(image).convert("RGBA")
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
    except OSError as error:
        parser.exit(1, f"{error}\n")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    for name, image in layouts.items():
        target = args.output_dir / f"{name}.png"
        image.save(target, optimize=True, icc_profile=srgb)
        print(f"{target.name} | {image.width} x {image.height}")


if __name__ == "__main__":
    main()
