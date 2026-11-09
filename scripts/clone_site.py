"""Create a locally navigable mirror of holdenroofing.com using the stdlib.

Usage: python scripts/clone_site.py
Output: ./clone/ (open clone/index.html or run `python -m http.server -d clone`)
"""
import hashlib
import json
import os
import posixpath
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urldefrag, urlsplit, unquote

ROOT = "https://holdenroofing.com/"
SITE_HOST = urlsplit(ROOT).hostname.lower()
SITE_HOSTS = {SITE_HOST, "www." + SITE_HOST}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clone")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
ASSET_RE = re.compile(
    r"""["']([^"'<>\\\s]+?\.(?:png|jpe?g|gif|svg|webp|ico|css|js|woff2?|ttf|eot|otf|mp4|webm|mp3|pdf|json|xml)(?:\?[^"'<>\\\s]*)?)["']""",
    re.I,
)
ATTR_RE = re.compile(
    r"""(\b(?:href|src|data-src|data-original|data-lazy-src|poster|data-background|background|action|data|content|style)\s*=\s*)(["'])(.*?)\2""",
    re.I | re.S,
)
SRCSET_RE = re.compile(r"""(\b(?:srcset|data-srcset)\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
CSS_URL_RE = re.compile(r"""url\(\s*(["']?)(.*?)\1\s*\)""", re.I | re.S)
CSS_IMPORT_RE = re.compile(r"""@import\s+(?:url\(\s*)?(["'])(.*?)\1\s*\)?""", re.I)

pages = {}
failed = {}


def normalize(url):
    url, _ = urldefrag(url.strip())
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    if host in SITE_HOSTS:
        scheme, netloc = "https", SITE_HOST
    else:
        scheme, netloc = parsed.scheme.lower(), parsed.netloc.lower()
    path = parsed.path or "/"
    if " " in path or ";charset" in path or "'" in path:
        return None
    return f"{scheme}://{netloc}{path}" + (f"?{parsed.query}" if parsed.query else "")


def is_site_url(url):
    return bool(url and urlsplit(url).hostname and urlsplit(url).hostname.lower() in SITE_HOSTS)


def local_path(url, content_type=""):
    parsed = urlsplit(url)
    path = unquote(parsed.path)
    if path.endswith("/") or not path:
        path += "index.html"
    _, ext = posixpath.splitext(path)
    if not ext and "html" in content_type.lower():
        path += ".html"
    if parsed.query:
        root, ext = posixpath.splitext(path)
        path = f"{root}__{hashlib.md5(parsed.query.encode()).hexdigest()[:8]}{ext}"
    if not is_site_url(url):
        path = posixpath.join("_external", parsed.netloc.lower(), path.lstrip("/"))
    path = posixpath.normpath("/" + path).lstrip("/")
    return re.sub(r'[<>:"|?*]', "_", path)


def fetch(url):
    safe_url = quote(url, safe="/:?=&%+~@!$'()*,;")
    request = urllib.request.Request(
        safe_url, headers={"User-Agent": UA, "Accept": "*/*"}
    )
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.geturl(), response.headers.get("Content-Type", ""), response.read()
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in (408, 425, 429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"request failed after retries: {last_error}") from last_error


def decode(data, content_type):
    match = re.search(r"charset=([\w-]+)", content_type, re.I)
    encodings = ([match.group(1)] if match else []) + ["utf-8", "cp1252"]
    for encoding in encodings:
        try:
            return data.decode(encoding), encoding
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", "replace"), "utf-8"


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.references.append((attrs["href"], False))
        if tag == "link" and attrs.get("href"):
            rel = set((attrs.get("rel") or "").lower().split())
            is_asset = bool(rel & {"stylesheet", "icon", "preload", "modulepreload", "manifest", "apple-touch-icon"})
            self.references.append((attrs["href"], is_asset))
        for name in ("src", "poster", "data-src", "data-original", "data-lazy-src",
                     "data-background", "data-bg", "background", "action", "data"):
            if attrs.get(name):
                self.references.append((attrs[name], True))
        for name in ("srcset", "data-srcset"):
            for item in (attrs.get(name) or "").split(","):
                bits = item.strip().split()
                if bits:
                    self.references.append((bits[0], True))
        if tag == "meta" and (attrs.get("property", "").lower() in
                              {"og:image", "og:video", "twitter:image", "twitter:player"}):
            if attrs.get("content"):
                self.references.append((attrs["content"], True))
        if attrs.get("style"):
            self.references.extend((match.group(2), True) for match in CSS_URL_RE.finditer(attrs["style"]))


def extract_references(text, base, content_type, is_html, is_css, is_js, is_xml):
    references = []
    if is_html:
        parser = ReferenceParser()
        parser.feed(text)
        references.extend(parser.references)
    if is_css or is_html:
        references.extend((match.group(2), True) for match in CSS_URL_RE.finditer(text))
        references.extend((match.group(2), True) for match in CSS_IMPORT_RE.finditer(text))
    if is_js:
        references.extend((match.group(1), True) for match in ASSET_RE.finditer(text))
    if is_xml:
        try:
            root = ET.fromstring(text)
            references.extend((element.text.strip(), False) for element in root.iter()
                              if element.tag.lower().endswith("loc") and element.text)
        except ET.ParseError:
            references.extend((url, False) for url in re.findall(r"https?://[^\s<>\"']+", text))
        if urlsplit(base).path.lower().endswith("robots.txt"):
            references.extend((match, False) for match in
                              re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text))
    return references


SKIP_PATH_RE = re.compile(
    r"^/(wp-json|xmlrpc\.php|wp-login\.php|wp-admin|wp-cron\.php|cart|checkout|my-account|new-cart|shop)(/|$)"
    r"|/feed/?$|/embed/?$|/trackback/?$|/comments/",
    re.I,
)
SKIP_QUERY_RE = re.compile(r"(^|&)(s|replytocom|add-to-cart|p|page_id|format|url|rest_route)=", re.I)


def should_skip(url):
    parsed = urlsplit(url)
    if not is_site_url(url):
        return False
    return bool(SKIP_PATH_RE.search(parsed.path) or SKIP_QUERY_RE.search(parsed.query))


def alternate_urls(url, error):
    if not is_site_url(url) or not isinstance(error, urllib.error.HTTPError):
        return []
    path = unquote(urlsplit(url).path)
    if error.code == 404 and path != "/" and not posixpath.splitext(path)[1] and not path.endswith("/"):
        return [url.rstrip("/") + "/"]
    return []

def crawl():
    queue = deque([normalize(ROOT), normalize(urljoin(ROOT, "robots.txt")),
                   normalize(urljoin(ROOT, "sitemap_index.xml"))])
    seen = set(queue)
    texts = {}

    while queue:
        url = queue.popleft()
        try:
            final, content_type, data = fetch(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, RuntimeError) as error:
            fallback_succeeded = False
            for candidate in alternate_urls(url, error):
                try:
                    final, content_type, data = fetch(candidate)
                    pages[candidate] = local_path(normalize(final), content_type)
                    seen.add(candidate)
                    print("ALT ", url, "->", candidate)
                    fallback_succeeded = True
                    break
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                        OSError, RuntimeError):
                    continue
            if not fallback_succeeded:
                failed[url] = f"{type(error).__name__}: {error}"
                print("FAIL", url, failed[url])
                continue

        final_url = normalize(final)
        if not final_url:
            failed[url] = f"redirected to unsupported URL: {final}"
            print("FAIL", url, failed[url])
            continue
        path = local_path(final_url, content_type)
        destination = os.path.join(OUT, *path.split("/"))
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as output:
            output.write(data)
        pages[url] = path
        pages[final_url] = path
        if final_url != url:
            pages[url] = path
        print("OK  ", path, len(data))

        extension = posixpath.splitext(path)[1].lower()
        is_html = extension in (".html", ".htm") or "html" in content_type.lower()
        is_css = extension == ".css" or "text/css" in content_type.lower()
        is_js = extension == ".js" or "javascript" in content_type.lower()
        is_xml = extension in (".xml", ".txt") or "xml" in content_type.lower()
        if not (is_html or is_css or is_js or is_xml):
            continue

        text, encoding = decode(data, content_type)
        if is_html or is_css or is_js:
            texts[path] = (final_url, encoding, is_css, is_js)
        if is_js and not is_site_url(final_url):
            continue
        for reference, asset_only in extract_references(
                text, final_url, content_type, is_html, is_css, is_js, is_xml):
            reference = reference.strip()
            if not reference or re.search(r"[\\\",\s]", reference) or reference.startswith(
                    ("data:", "mailto:", "tel:", "javascript:", "#", "blob:")):
                continue
            target = normalize(urljoin(final_url, reference))
            if not target or target in seen or should_skip(target):
                continue
            if is_site_url(target) or asset_only:
                seen.add(target)
                queue.append(target)
    return texts


def rewrite(texts):
    def local_reference(reference, base, here):
        value = reference.strip()
        if not value or value.startswith(
                ("data:", "mailto:", "tel:", "javascript:", "#", "blob:")):
            return reference
        fragment = ""
        if "#" in value:
            value, suffix = value.split("#", 1)
            fragment = "#" + suffix
        target = normalize(urljoin(base, value))
        if not target or target not in pages:
            return reference
        relative = posixpath.relpath(pages[target], here or ".")
        return relative.replace(" ", "%20") + fragment

    for path, (base, encoding, is_css, is_js) in texts.items():
        destination = os.path.join(OUT, *path.split("/"))
        with open(destination, "rb") as source:
            text, _ = decode(source.read(), f"charset={encoding}")
        here = posixpath.dirname(path)

        def attr(match):
            value = local_reference(match.group(3), base, here)
            return f"{match.group(1)}{match.group(2)}{value}{match.group(2)}"

        def srcset(match):
            parts = []
            for part in match.group(3).split(","):
                bits = part.strip().split()
                if bits:
                    bits[0] = local_reference(bits[0], base, here)
                    parts.append(" ".join(bits))
            return f"{match.group(1)}{match.group(2)}{', '.join(parts)}{match.group(2)}"

        def css_url(match):
            value = local_reference(match.group(2), base, here)
            return f"url({match.group(1)}{value}{match.group(1)})"

        def css_import(match):
            value = local_reference(match.group(2), base, here)
            return f"@import {match.group(1)}{value}{match.group(1)}"

        text = ATTR_RE.sub(attr, text)
        text = SRCSET_RE.sub(srcset, text)
        text = CSS_URL_RE.sub(css_url, text)
        text = CSS_IMPORT_RE.sub(css_import, text)
        if is_js:
            def js_url(match):
                value = local_reference(match.group(1), base, here)
                return match.group(0).replace(match.group(1), value, 1)
            text = ASSET_RE.sub(js_url, text)
        with open(destination, "w", encoding=encoding, errors="xmlcharrefreplace", newline="") as output:
            output.write(text)


def main():
    os.makedirs(OUT, exist_ok=True)
    texts = crawl()
    rewrite(texts)
    manifest = {
        "root": ROOT,
        "files": sorted(set(pages.values())),
        "pages": sorted(path for path in set(pages.values())
                        if path.lower().endswith((".html", ".htm"))),
        "failed": failed,
    }
    with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2)
    print(f"\nDone: {len(manifest['files'])} files, "
          f"{len(manifest['pages'])} HTML pages, {len(failed)} failures")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
