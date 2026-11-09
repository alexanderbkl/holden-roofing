"""Check built pages in the repo root: local hrefs/srcs resolve, #anchors exist, images have alt, ids unique."""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
ids = {}
problems = []


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.imgs = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        for key in ("href", "src", "poster"):
            if a.get(key):
                self.refs.append(a[key])
        for key in ("srcset", "imagesrcset"):
            if a.get(key):
                self.refs.extend(part.strip().split()[0] for part in a[key].split(",") if part.strip())
        if tag == "img" and "alt" not in a:
            self.imgs.append(a.get("src"))
        if tag == "use" and a.get("href"):
            self.refs.append(a["href"])


scans = {}
for page in pages:
    scan = Scan()
    with open(os.path.join(ROOT, page), encoding="utf-8") as handle:
        scan.feed(handle.read())
    scans[page] = scan
    dup = {i for i in scan.ids if scan.ids.count(i) > 1}
    if dup:
        problems.append(f"{page}: duplicate ids {sorted(dup)}")
    problems.extend(f"{page}: img without alt {src}" for src in scan.imgs)

for page, scan in scans.items():
    for ref in scan.refs:
        if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "javascript:")):
            continue
        parts = urlsplit(ref)
        path, fragment = unquote(parts.path), parts.fragment
        if not path:
            target = page
        else:
            target = path
            if not os.path.exists(os.path.join(ROOT, target)):
                problems.append(f"{page}: missing {ref}")
                continue
        if fragment and target.endswith(".html") and not fragment.startswith("i-") and fragment not in scans[target].ids:
            problems.append(f"{page}: missing anchor {ref}")
        if fragment.startswith("i-") and fragment not in scans[page].ids and f'id="{fragment}"' not in open(os.path.join(ROOT, page), encoding="utf-8").read():
            problems.append(f"{page}: missing icon {ref}")

print(len(pages), "pages;", len(problems), "problems")
print("\n".join(sorted(set(problems))[:40]))
sys.exit(1 if problems else 0)
