# Holden Roofing — website redesign

A static, framework-free redesign of [holdenroofing.com](https://holdenroofing.com): plain HTML5, modern CSS and vanilla JavaScript. Deploys as-is to GitHub Pages (`.nojekyll` is included) — no Node build, no backend.

## What's in the box

| Path | Purpose |
|---|---|
| `*.html` (repo root) | Built pages: home, residential, commercial, storm damage, locations, reviews, financing, about, contact, privacy, 404 |
| `assets/css/styles.css` | Design system (navy + crimson from the logo, Fraunces + Inter, mobile-first) |
| `assets/js/app.js` | Nav drawer, scroll reveals, count-ups, materials tabs, review carousel, lightbox, financing estimator, interactive Texas office map, forms |
| `assets/img`, `assets/fonts` | Optimized WebP photos (from the live site), logo, self-hosted fonts |
| `src/` | Page sources + shared partials (map, reviews, estimator, CTA form) |
| `scripts/` | One-time tooling (Python): `clone_site.py`, `audit_content.py`, `build_assets.py`, `build_site.py`, `check_site.py` |
| `clone/`, `audit/` | Local mirror of the original site and extracted content (git-ignored; `audit/business_facts.md` summarizes the facts used) |

## Editing & rebuilding

Pages are generated from `src/pages/*.html` so the header/footer/map stay in sync:

```powershell
python scripts\build_site.py    # regenerates the root *.html, sitemap.xml, robots.txt
python scripts\check_site.py    # verifies links, anchors, icons and image alt text
python -m http.server 8000      # preview at http://localhost:8000
```

`python scripts\build_assets.py` re-creates the optimized images from `clone/` (needs `pip install pillow`).

## Before going live

- **Site URL** — set `SITE_URL` in `scripts/build_site.py` (canonical, sitemap, social cards), then rebuild.
- **Lead form** — in `assets/js/app.js`, `CONFIG.endpoint` can point at a form service (e.g. Formspree). Without it, the form opens the visitor's email app addressed to `CONFIG.email`; confirm which inbox the owners want.
- **Maps** — the office map embeds Google Maps lazily; it needs an internet connection (everything else works offline).
- **Reviews** — review excerpts are copied from the public Google reviews on the existing site.
- **Pricing** — the original site publishes no prices, so none are invented. The financing estimator uses the advertised terms (Service Financial, 9.99% APR, 120 months, $3,000–$100,000, approved credit).
- **Payments** — "Make a Payment" links to the existing Clover payment portal.

## Deploy to GitHub Pages

Push to the repository and enable Pages (branch `main`, folder `/`). All links are relative, so it works from a project sub-path.
