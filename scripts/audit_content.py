"""Extract page copy, business details, legal references and image metadata from ./clone."""
import csv
import html
import json
import os
import re
import struct
from html.parser import HTMLParser

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CLONE = os.path.join(BASE, "clone")
AUDIT = os.path.join(BASE, "audit")
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\w)"
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SOCIAL_RE = re.compile(
    r"https?://(?:www\.)?(?:instagram|facebook|linkedin|youtube|x|twitter|"
    r"tiktok|pinterest|nextdoor)\.[^\s\"'<>)]*",
    re.I,
)
SERVICE_TERMS = re.compile(
    r"\b(?:roof(?:ing|s)?|shingles?|remodel(?:ing|ling)?|"
    r"storm damage|leak(?:s| prevention)?|gutter(?:s|ing)?|"
    r"repair(?:s)?|replacement|inspection|emergency)\b",
    re.I,
)
PRICE_TERMS = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\.\d{2})?|\b(?:free|complimentary)\s+"
    r"(?:estimate|inspection|quote)|\bpricing\b|\bcost\b|\brate\b|\bquotes?\b)",
    re.I,
)
LEGAL_TERMS = re.compile(r"\b(?:privacy|terms|conditions|legal|disclaimer)\b", re.I)
TERMS_RE = re.compile(r"\b(?:terms(?:-of-use)?|conditions)\b", re.I)
JSONLD_RE = re.compile(
    r"""<script\b(?=[^>]*\btype\s*=\s*["']application/ld\+json["'])[^>]*>(.*?)</script>""",
    re.I | re.S,
)


class TextExtractor(HTMLParser):
    BLOCK = {
        "p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
        "tr", "section", "article", "address", "footer", "header",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skipped = []
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self.skipped.append(tag)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attributes.get("name", "").lower() in (
                "description", "keywords"):
            self.meta[attributes["name"].lower()] = attributes.get("content", "")
        if tag == "img":
            src = attributes.get("src") or attributes.get("data-src") or ""
            alt = (attributes.get("alt") or "").strip()
            self.images.append({"src": src, "alt": alt})
            if alt:
                self.out.append(f"[Image: {alt}]")
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in ("script", "style", "noscript") and tag in self.skipped:
            self.skipped.reverse()
            self.skipped.remove(tag)
            self.skipped.reverse()
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skipped:
            self.out.append(data)


def read(path):
    with open(path, "rb") as source:
        raw = source.read()
    for encoding in ("utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def image_size(path):
    try:
        with open(path, "rb") as source:
            header = source.read(32)
            if header[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", header[16:24])
            if header[:6] in (b"GIF87a", b"GIF89a"):
                return struct.unpack("<HH", header[6:10])
            if header[:2] == b"\xff\xd8":
                source.seek(2)
                while True:
                    marker_start = source.read(1)
                    while marker_start and marker_start != b"\xff":
                        marker_start = source.read(1)
                    while marker_start == b"\xff":
                        marker_start = source.read(1)
                    if not marker_start:
                        return None
                    marker = marker_start[0]
                    if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                        source.read(3)
                        height, width = struct.unpack(">HH", source.read(4))
                        return width, height
                    segment_length = struct.unpack(">H", source.read(2))[0]
                    source.seek(segment_length - 2, 1)
    except (OSError, struct.error):
        return None
    return None


def structured_business_records(source):
    records = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("@type") in ("LocalBusiness", "RoofingContractor"):
                address = value.get("address") or {}
                if isinstance(address, dict):
                    address_parts = (
                        address.get("streetAddress"),
                        address.get("addressLocality"),
                        address.get("addressRegion"),
                        address.get("postalCode"),
                    )
                    address = ", ".join(part for part in address_parts if part) if any(
                        (address.get(key) for key in
                         ("streetAddress", "addressLocality", "postalCode"))
                    ) else ""
                records.append({
                    "name": value.get("name", ""),
                    "telephone": value.get("telephone", ""),
                    "email": value.get("email", ""),
                    "address": address,
                    "price_range": value.get("priceRange", ""),
                    "opening_hours": value.get("openingHours", ""),
                    "payment_accepted": value.get("paymentAccepted", ""),
                })
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for block in JSONLD_RE.findall(source):
        try:
            visit(json.loads(block))
        except json.JSONDecodeError:
            continue
    return records


def main():
    if not os.path.isdir(CLONE):
        raise FileNotFoundError(f"Clone directory not found: {CLONE}. Run clone_site.py first.")
    pages_dir = os.path.join(AUDIT, "pages_text")
    os.makedirs(pages_dir, exist_ok=True)
    summary = {
        "pages": [],
        "emails": set(),
        "phones": set(),
        "social": set(),
        "addresses": set(),
        "locations": set(),
        "services": set(),
        "pricing_mentions": set(),
        "legal_pages": [],
        "terms_of_service_pages": [],
        "business_data": {},
        "images": [],
    }
    image_rows = []

    for root, _, files in os.walk(CLONE):
        for filename in sorted(files):
            path = os.path.join(root, filename)
            relative = os.path.relpath(path, CLONE).replace("\\", "/")
            extension = os.path.splitext(filename)[1].lower()
            if extension in IMAGE_EXTENSIONS:
                size = image_size(path)
                image_rows.append({
                    "file": relative,
                    "bytes": os.path.getsize(path),
                    "width": size[0] if size else "",
                    "height": size[1] if size else "",
                })
            if extension not in (".html", ".htm"):
                continue

            source = read(path)
            parser = TextExtractor()
            parser.feed(source)
            body = html.unescape("".join(parser.out))
            body = re.sub(r"[ \t\u00a0]+", " ", body)
            body = re.sub(r"\n\s*\n+", "\n", body).strip()
            output_path = os.path.join(pages_dir, relative.replace("/", "__") + ".txt")
            with open(output_path, "w", encoding="utf-8", newline="\n") as output:
                output.write(
                    f"URL: {relative}\nTITLE: {parser.title.strip()}\n"
                    f"DESCRIPTION: {parser.meta.get('description', '')}\n"
                    f"KEYWORDS: {parser.meta.get('keywords', '')}\n\n{body}\n"
                )

            summary["pages"].append({
                "file": relative,
                "title": parser.title.strip(),
                "description": parser.meta.get("description", ""),
                "chars": len(body),
            })
            summary["emails"].update(EMAIL_RE.findall(source))
            for phone in PHONE_RE.findall(source):
                digits = re.sub(r"\D", "", phone)
                if len(digits) == 11 and digits.startswith("1"):
                    digits = digits[1:]
                if len(digits) == 10:
                    summary["phones"].add(
                        f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                    )
                else:
                    summary["phones"].add(phone)
            for record in structured_business_records(source):
                key = (str(record["name"]), str(record["address"]))
                if key not in summary["business_data"]:
                    summary["business_data"][key] = {**record, "pages": set()}
                else:
                    for field, value in record.items():
                        if value and not summary["business_data"][key][field]:
                            summary["business_data"][key][field] = value
                summary["business_data"][key]["pages"].add(relative)
            summary["social"].update(SOCIAL_RE.findall(source))
            for sentence in re.split(r"[\r\n.!?]+", body):
                sentence = sentence.strip()
                if SERVICE_TERMS.search(sentence):
                    summary["services"].add(sentence)
                if PRICE_TERMS.search(sentence):
                    summary["pricing_mentions"].add(sentence)
                if re.search(r"\b(?:Texas|TX)\b", sentence, re.I):
                    summary["locations"].add(sentence)
                if re.search(r"\b\d{1,6}\s+[\w.'-]+(?:\s+[\w.'-]+){0,5}\s"
                             r"(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|"
                             r"Drive|Dr|Lane|Ln|Highway|Hwy)\b", sentence, re.I):
                    summary["addresses"].add(sentence)
            if LEGAL_TERMS.search(relative) or LEGAL_TERMS.search(parser.title):
                legal_page = {
                    "file": relative,
                    "title": parser.title.strip(),
                }
                summary["legal_pages"].append(legal_page)
                if TERMS_RE.search(relative) or TERMS_RE.search(parser.title):
                    summary["terms_of_service_pages"].append(legal_page)
            summary["images"].extend(
                {"page": relative, **image} for image in parser.images if image["src"] or image["alt"]
            )

    image_rows.sort(key=lambda row: (-row["bytes"], row["file"]))
    with open(os.path.join(AUDIT, "images.csv"), "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["file", "bytes", "width", "height"])
        writer.writeheader()
        writer.writerows(image_rows)

    for key, value in summary.items():
        if isinstance(value, set):
            summary[key] = sorted(value)
    summary["business_data"] = sorted(
        (
            {**record, "pages": sorted(record["pages"])}
            for record in summary["business_data"].values()
        ),
        key=lambda record: (str(record["name"]), str(record["address"])),
    )
    summary["pages"].sort(key=lambda page: page["file"])
    summary["legal_pages"].sort(key=lambda page: page["file"])
    summary["terms_of_service_pages"].sort(key=lambda page: page["file"])
    summary["images"].sort(key=lambda image: (image["page"], image["src"]))
    summary["image_files"] = len(image_rows)
    summary["has_published_prices"] = any(
        re.search(r"\$\s?\d", mention) for mention in summary["pricing_mentions"]
    )
    with open(os.path.join(AUDIT, "summary.json"), "w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2, ensure_ascii=False)
    print(f"{len(summary['pages'])} pages; {len(image_rows)} images; "
          f"{len(summary['emails'])} emails; {len(summary['phones'])} phone numbers")


if __name__ == "__main__":
    main()
