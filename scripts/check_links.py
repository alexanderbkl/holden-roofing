"""Verify every relative href/src in ./clone resolves to a local file."""
import os
import re
import time
from urllib.parse import unquote, urlsplit

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clone"))
ATTR = re.compile(r"""\b(?:href|src|poster)\s*=\s*["']([^"'\s]+)["']""", re.I)
SKIP = ("#", "mailto:", "tel:", "data:", "javascript:", "sms:")

bad, pages = {}, 0
for directory, _, files in os.walk(ROOT):
    for name in files:
        if not name.endswith(".html"):
            continue
        pages += 1
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        started = time.time()
        found = ATTR.findall(text)
        if time.time() - started > 1:
            print("slow:", path, len(text), flush=True)
        for url in found:
            if url.startswith(SKIP):
                continue
            if url.startswith(("http:", "https:", "//")):
                host = urlsplit(url if not url.startswith("//") else "https:" + url).hostname or ""
                if host.endswith("holdenroofing.com"):
                    bad.setdefault("ABSOLUTE " + url, []).append(os.path.relpath(path, ROOT))
                continue
            target = os.path.normpath(os.path.join(directory, unquote(urlsplit(url).path)))
            if os.path.isdir(target):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                bad.setdefault(url, []).append(os.path.relpath(path, ROOT))

IGNORE = re.compile(r"/(feed|wp-json|xmlrpc|shop|cart|checkout)\b|cookie-law-info|widget-google-reviews|easy-upload|about:blank")
print(f"{pages} pages checked, {len(bad)} distinct unresolved references")
shown = 0
for url, where in sorted(bad.items(), key=lambda item: -len(item[1])):
    if IGNORE.search(url):
        continue
    print(f"{len(where):4d}  {url[:100]}  (e.g. {where[0]})")
    shown += 1
    if shown >= 40:
        break
