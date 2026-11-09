"""One-time asset prep: optimized WebP photos + logo + social image from ./clone.

Needs Pillow (`pip install pillow`) at build time only; the shipped site is pure static.
Fonts (Fraunces + Inter, latin subset) are already committed in assets/fonts; pass --fonts to re-download.
Usage: python scripts/build_assets.py [--fonts]
"""
import os
import re
import sys
import urllib.request

from PIL import Image

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
UPLOADS = os.path.join(BASE, "clone", "wp-content", "uploads")
IMG = os.path.join(BASE, "assets", "img")
FONTS = os.path.join(BASE, "assets", "fonts")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
FONT_CSS = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;"
            "1,9..144,400..600&family=Inter:wght@400..700&display=swap")

WIDE = (640, 1200)
CARD = (480, 960)
# output name -> (path under wp-content/uploads, widths)
PHOTOS = {
    "hero": ("2026/09/DJI_20260806125252_0059_D.jpg", (480, 960, 1600)),
    "inspect": ("2026/09/028_frank_shngl_swatch_ladder_a.jpg", WIDE),
    "install": ("2026/09/IR1A1987.jpg", WIDE),
    "ladder": ("2026/09/033_frank_carry_ladder.jpg", WIDE),
    "truck": ("2026/09/IR1A2203.jpg", WIDE),
    "sign": ("2026/09/IR1A1963-Edit.jpg", WIDE),
    "team": ("2026/09/ONBY1491.jpg", WIDE),
    "awards": ("2026/09/IR1A4898-Enhanced-NR.jpg", WIDE),
    "van": ("2026/09/004_3sales_van_sdlft_a.jpg", WIDE),
    "shingle": ("2026/09/DJI_20260722141817_0093_D_edit.jpg", WIDE),
    "shingle-pool": ("2026/09/DJI_20260722142510_0136_D.jpg", CARD),
    "shingle-dark": ("2026/09/roofshowcase_charlesohaeri_04.jpg", CARD),
    "tile": ("2026/09/tileafter_04.jpg", WIDE),
    "tile-villa": ("2026/09/tileafter_02.jpg", CARD),
    "metal": ("2026/09/metalshowcase_01.jpg", WIDE),
    "metal-brown": ("2026/09/metalshowcase_05.jpg", CARD),
    "metal-blue": ("2026/09/DJI_20260629173056_0009_D.jpg", WIDE),
    "metal-blue-top": ("2026/09/DJI_20260629174259_0073_D.jpg", CARD),
    "metal-slate": ("2026/09/vongoten_04_edit.jpg", CARD),
    "copper": ("2026/09/roofcopper_01.jpg", WIDE),
    "damage": ("2026/08/IR1A0042_edit-scaled.png", WIDE),
    "hail": ("2026/08/damage_01.jpeg", CARD),
    "tile-damage": ("2026/08/tiledamage_01.jpeg", CARD),
    "commercial": ("2026/05/roofing_checklist_fin_img-scaled.jpg", WIDE),
    "neighborhood": ("2026/09/DJI_20260722142001_0101_D.jpg", WIDE),
    "loc-houston": ("2026/02/location.jpg", (800,)),
    "loc-austin": ("2026/03/austin-img.jpg", (800,)),
    "loc-san-antonio": ("2026/03/San-Antonio-banner.jpg", (800,)),
    "loc-san-marcos": ("2026/03/San-Marcos-Texas-Aerial.jpg", (800,)),
    "loc-dallas": ("2026/03/dallas-banner.jpg", (800,)),
    "loc-spring": ("2026/03/spring-texas-banner.jpg", (800,)),
    "loc-temple": ("2026/03/temple_website_bg.png", (800,)),
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
        with open(os.path.join(FONTS, wanted[(family, style)]), "wb") as out:
            out.write(get(url))
        print("font", wanted[(family, style)])


def save(image, name, width, quality, fmt="WEBP"):
    height = round(image.height * width / image.width)
    resized = image if width >= image.width else image.resize((width, height), Image.LANCZOS)
    ext = "webp" if fmt == "WEBP" else "jpg"
    path = os.path.join(IMG, f"{name}-{width}.{ext}" if width else f"{name}.{ext}")
    resized.save(path, fmt, quality=quality, **({"method": 6} if fmt == "WEBP" else {"optimize": True}))
    print("img", os.path.basename(path), os.path.getsize(path) // 1024, "KB")


def photos():
    os.makedirs(IMG, exist_ok=True)
    for name, (source, widths) in PHOTOS.items():
        image = Image.open(os.path.join(UPLOADS, *source.split("/"))).convert("RGB")
        for width in widths:
            save(image, name, width, 72 if name == "hero" else 76)

    logo = Image.open(os.path.join(UPLOADS, "2026", "01", "3d-logo-holden_roofingx-3.png")).convert("RGBA")
    for width in (200, 400):
        save(logo, "logo", width, 90)

    hero = Image.open(os.path.join(UPLOADS, *PHOTOS["hero"][0].split("/"))).convert("RGB")
    og = hero.crop((0, 245, 2000, 245 + 1050)).resize((1200, 630), Image.LANCZOS)
    og_path = os.path.join(IMG, "og.jpg")
    og.save(og_path, quality=82, optimize=True)
    print("img og.jpg", os.path.getsize(og_path) // 1024, "KB")


if __name__ == "__main__":
    if "--fonts" in sys.argv:
        fonts()
    photos()
