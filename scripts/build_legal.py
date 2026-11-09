"""Generate privacy.html from the original site's privacy text (audit/pages_text).

The legacy site publishes a privacy statement per city (all identical) and no terms of service,
so only the privacy page is produced. Run `python scripts/audit_content.py` first.
"""
import html
import os
import re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(BASE, "audit", "pages_text", "austin__privacy-statement.html.txt")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Privacy Policy — Robinson &amp; Sons Roofing &amp; Remodeling</title>
  <meta name="robots" content="noindex,follow">
  <link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
<header class="site-header solid">
  <div class="container nav">
    <a href="index.html" class="brand" aria-label="Robinson &amp; Sons Roofing &amp; Remodeling — home">
      <svg class="brand-mark" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="10" fill="currentColor"/><path d="M7 21 20 9l13 12" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 22.5V31h16v-8.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" opacity=".55"/></svg>
      <span class="brand-text"><b>Robinson <em>&amp;</em> Sons</b><small>Roofing &amp; Remodeling</small></span>
    </a>
    <a class="btn btn-primary btn-sm" href="index.html#quote">Request a Quote</a>
  </div>
</header>
<main class="legal">
  <div class="container">
    <a class="back" href="index.html">&larr; Home</a>
    <h1>Privacy Policy</h1>
{body}
  </div>
</main>
<footer class="site-footer" style="padding-bottom:3rem">
  <div class="container footer-bottom" style="margin-top:0;border-top:0;padding-top:0">
    <span>© Robinson &amp; Sons Roofing &amp; Remodeling. All rights reserved.</span>
    <a href="index.html">Back to home</a>
  </div>
</footer>
</body>
</html>
"""


def main():
    with open(SRC, encoding="utf-8") as source:
        lines = [line.strip() for line in source.read().splitlines()]
    start = lines.index("Our Privacy Policy") + 1
    end = lines.index("Contact Us", start)
    paragraphs = []
    for line in lines[start:end]:
        if not line:
            continue
        text = html.escape(line)
        text = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" rel="noopener">\1</a>', text)
        paragraphs.append(f"    <p>{text}</p>")
    with open(os.path.join(BASE, "privacy.html"), "w", encoding="utf-8", newline="\n") as output:
        output.write(PAGE.format(body="\n".join(paragraphs)))
    print("privacy.html:", len(paragraphs), "paragraphs")


if __name__ == "__main__":
    main()
