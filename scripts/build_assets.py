"""One-time asset prep for the redesign: self-hosted fonts + optimized WebP photos.

Needs Pillow (`pip install pillow`) at build time only; the shipped site is pure static.
Usage: python scripts/build_assets.py
"""
import os
import re
import urllib.request

from PIL import Image

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CLONE = os.path.join(BASE, "clone")
IMG = os.path.join(BASE, "assets", "img")
FONTS = os.path.join(BASE, "assets", "fonts")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
FONT_CSS = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;"
            "1,9..144,400..600&family=Inter:wght@400..700&display=swap")

# source photo -> (output name, widths)
PHOTOS = {
    "media/robinsonroofingHeader1-0.jpg": ("hero", (640, 1200)),
    "austin/images/austin-header1company-0.jpg": ("crew", (640, 1200)),
    "media/san-antonio-RoofingHeader1-0.jpg": ("build", (640, 1200)),
}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()


def fonts():
    os.makedirs(FONTS, exist_ok=True)
    css = get(FONT_CSS).decode()
    wanted = {("Fraunces", "normal"): "fraunces.woff2", ("Fraunces", "italic"): "fraunces-italic.woff2",
              ("Inter", "normal"): "inter.woff2"}
    for subset, block in re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset != "latin":
            continue
        family = re.search(r"font-family: '([^']+)'", block).group(1)
        style = re.search(r"font-style: (\w+)", block).group(1)
        url = re.search(r"url\((.*?)\)", block).group(1)
        name = wanted[(family, style)]
        with open(os.path.join(FONTS, name), "wb") as out:
            out.write(get(url))
        print("font", name)


def photos():
    os.makedirs(IMG, exist_ok=True)
    for src, (name, widths) in PHOTOS.items():
        image = Image.open(os.path.join(CLONE, *src.split("/"))).convert("RGB")
        for width in widths:
            height = round(image.height * width / image.width)
            resized = image if width >= image.width else image.resize((width, height), Image.LANCZOS)
            path = os.path.join(IMG, f"{name}-{width}.webp")
            resized.save(path, "WEBP", quality=80, method=6)
            print("img", os.path.basename(path), os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    fonts()
    photos()
