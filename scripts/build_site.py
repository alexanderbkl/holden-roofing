"""Static site generator for Holden Roofing (one-time build step; output is plain HTML/CSS/JS).

Pages live in src/pages/*.html (a front-matter comment + body), shared fragments in src/partials/.
Usage: python scripts/build_site.py      -> writes *.html, sitemap.xml and robots.txt in the repo root
"""
import math
import os
import re
from urllib.parse import urlparse
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "src")
SITE_URL = "https://alexanderbkl.github.io/holden-roofing/"  # change when the real domain is known
PHONE = "888.553.1318"
TEL = "+18885531318"
PAY_URL = "https://www.clover.com/pay-widgets/ef9603eb-15af-4ef0-b131-ffffbd06c5fc"
SOCIAL = [
    ("facebook", "https://www.facebook.com/myholdenroofing", "Facebook"),
    ("instagram", "https://www.instagram.com/holdenroofingtx/", "Instagram"),
    ("linkedin", "https://www.linkedin.com/company/holden-roofing-inc/", "LinkedIn"),
    ("youtube", "https://www.youtube.com/@holdenroofingtx", "YouTube"),
]

OFFICES = [
    dict(key="houston", name="Houston", tag="Main office", street="2128 1st Street", city="Rosenberg, TX 77471",
         phone="(281) 344-9083", img="loc-houston", lat=29.557, lon=-95.808, label=(22, 8, "start"),
         meta="4.8 Google rating · 916+ reviews", blurb="Our home base for the Greater Houston area, serving families here since 1961."),
    dict(key="spring", name="Spring", tag="North Houston", street="17207 Kuykendahl Rd. Ste. 110", city="Spring, TX 77379",
         phone="(281) 344-9083", img="loc-spring", lat=30.08, lon=-95.42, label=(20, -6, "start"),
         meta="", blurb="Roof repair and full replacements for Spring and the surrounding neighborhoods."),
    dict(key="austin", name="Austin", tag="Central Texas", street="111 W Anderson Ln, Suite E360A", city="Austin, TX 78752",
         phone="(512) 750-0523", img="loc-austin", lat=30.327, lon=-97.717, label=(-20, -6, "end"),
         meta="4.6 Google rating", blurb="Serving Austin and Hill Country communities from Georgetown to Buda."),
    dict(key="san-antonio", name="San Antonio", tag="South Texas", street="1550 NE Loop 410, Suite 202", city="San Antonio, TX 78209",
         phone="(210) 630-9322", img="loc-san-antonio", lat=29.50, lon=-98.46, label=(-20, 8, "end"),
         meta="", blurb="Residential and commercial roofing across the San Antonio metro."),
    dict(key="san-marcos", name="San Marcos", tag="I-35 corridor", street="326 Cheatham St. Suite 104", city="San Marcos, TX 78666",
         phone="(512) 250-5981", img="loc-san-marcos", lat=29.88, lon=-97.94, label=(-20, 8, "end"),
         meta="", blurb="Built for San Marcos heat, heavy rain and fast-moving storms."),
    dict(key="temple", name="Temple", tag="Central Texas", street="6102 S General Bruce Dr", city="Temple, TX 76502",
         phone="(254) 495-4690", img="loc-temple", lat=31.07, lon=-97.37, label=(20, 8, "start"),
         meta="", blurb="Repairs, replacements and new construction roofing in the Temple area."),
    dict(key="dallas", name="Dallas", tag="North Texas", street="2775 Villa Creek Dr #145", city="Dallas, TX 75234",
         phone="(972) 510-8242", img="loc-dallas", lat=32.93, lon=-96.89, label=(20, 8, "start"),
         meta="", blurb="Our North Texas crew for Dallas homes and commercial properties."),
]

SERVICE_AREAS = {
    "Houston & Rosenberg area": ["Rosenberg", "Katy", "Sugar Land", "Missouri City", "Richmond", "Fulshear", "Stafford", "Sealy",
                                 "Wharton", "Needville", "Simonton", "Arcola", "Beasley", "Cinco Ranch", "East Bernard", "Fresno",
                                 "Pecan Grove", "Sienna", "Wallis", "Weston Lakes"],
    "Austin area": ["Austin", "Round Rock", "Cedar Park", "Georgetown", "Leander", "Pflugerville", "Lakeway", "Bee Cave", "Dripping Springs",
                    "Buda", "Kyle", "Hutto", "Manor", "Taylor", "Liberty Hill", "Bastrop", "Elgin", "Lago Vista", "Del Valle",
                    "Rollingwood", "Westlake Hills"],
}

NAV = [
    ("roofing", "Roofing", None),
    ("locations", "Locations", "locations.html"),
    ("reviews", "Reviews", "reviews.html"),
    ("financing", "Financing", "financing.html"),
    ("about", "About", "about.html"),
    ("contact", "Contact", "contact.html"),
]
ROOFING_MENU = [
    ("residential-roofing.html", "Residential Roofing", "Repair, replacement and new roofs for your home", "home"),
    ("commercial-roofing.html", "Commercial Roofing", "Low-slope, metal and coatings for businesses", "building"),
    ("storm-damage-repair.html", "Storm Damage Repair", "Inspections, tarping and claim guidance", "storm"),
]

REVIEWS = [
    ("Toyin Adeogba", "6 months ago", "I’m so glad we chose Holden Roofing for our roof replacement. Scott went above and beyond to ensure everything ran smoothly—from securing HOA approval to final completion. The team was efficient, thorough, and highly professional throughout the entire process."),
    ("Leon Booker", "7 months ago", "I am extremely satisfied with the services completed. Service was outstanding. Clean up outstanding. Communication outstanding. My roof was replaced to perfection. My gutters were installed to perfection. The work was completed in one day."),
    ("Jinsoo Kim", "7 months ago", "We had a very good experience with Holden Roofing. Their pricing was significantly better than the other quotes we received, the work was completed in a timely manner, and the quality of the job was excellent."),
    ("Phillip Smith", "7 months ago", "I worked with Frank Kastl. He was a great communicator and consummate professional. He stuck to all his timelines and got everything done. We are satisfied with our new roof. We would recommend."),
    ("Malee Wong", "7 months ago", "The house we bought had many roof issues, and Maynard Lanham was great at giving us our options, making his recommendations, and managing our chosen project. The whole team is very courteous, efficient, and friendly, too! We are happy customers!!"),
    ("Da Mora", "9 months ago", "I first filed a claim with my insurance back in 2019, but my hail and wind damage claims were repeatedly denied. Throughout that entire process, Holden Roofing was right there to help. Their crew is incredibly professional; they left no trash behind and ensured there was no damage to my lawn or landscaping."),
    ("Becky Covell", "9 months ago", "My representative, Michael Marino, went out of his way to explain everything that we were doing, and why. Michael was prompt to answer questions and respond. Further, he took the time to check in after the install to see if everything was going well."),
    ("Carol Neuszer", "9 months ago", "Holden came out early one morning, got the job completed in one day including total cleanup. The whole crew was amazing! When you have a roof leak, call Stan! He’ll come out and place a tarp on your roof right away."),
    ("David Houston", "11 months ago", "Scott and the team at Holden responded immediately, inspected my roof within a couple days, answered all of my questions quickly, guided me through what can be a scary process, and secured me a new roof, while also handling almost everything with the insurance company."),
]

ICONS = {
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "star": '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "building": '<path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4M9 9v.01M9 12v.01M9 15v.01M9 18v.01"/>',
    "storm": '<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><path d="m13 11-4 6h6l-4 6"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "menu": '<path d="M3 7h18M3 12h18M3 17h18"/>',
    "close": '<path d="M18 6 6 18M6 6l12 12"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "award": '<circle cx="12" cy="8" r="7"/><path d="m8.21 13.89-1.21 9.11 5-3 5 3-1.21-9.12"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/><path d="m9 14 2 2 4-4"/>',
    "dollar": '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
    "nav": '<path d="m3 11 19-9-9 19-2-8-8-2z"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5M2 12l10 5 10-5"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94z"/>',
    "camera": '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
    "heart": '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>',
    "facebook": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37zM17.5 6.5h.01"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/>',
    "youtube": '<path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"/><path d="m9.75 15.02 5.75-3.27-5.75-3.27z"/>',
}


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8") as handle:
        return handle.read()


def icon(name, fill=False):
    return f'<svg class="i{" i--fill" if fill else ""}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


def sprite():
    symbols = "".join(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>' for name, body in ICONS.items())
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>{symbols}</defs></svg>'


def expand_icons(html):
    return re.sub(r"\{\{i:([\w-]+)(:fill)?\}\}", lambda m: icon(m.group(1), bool(m.group(2))), html)


def stars(count=5):
    return f'<span class="stars" role="img" aria-label="{count} out of 5 stars">' + icon("star", True) * count + "</span>"


# ---- Texas map -------------------------------------------------------------------------------
TEXAS = [(-103.04, 36.50), (-100.00, 36.50), (-100.00, 34.56), (-99.75, 34.38), (-99.25, 34.21), (-98.75, 34.15), (-98.45, 34.08),
         (-97.95, 33.90), (-97.45, 33.82), (-97.15, 33.74), (-96.65, 33.84), (-96.20, 33.78), (-95.85, 33.93), (-95.25, 33.88),
         (-94.75, 33.75), (-94.48, 33.64), (-94.04, 33.55), (-94.04, 31.99), (-93.82, 31.78), (-93.70, 31.50), (-93.60, 31.18),
         (-93.53, 30.93), (-93.70, 30.40), (-93.72, 30.05), (-93.84, 29.69), (-94.35, 29.55), (-94.75, 29.35), (-95.15, 29.05),
         (-95.65, 28.75), (-96.30, 28.40), (-96.80, 28.15), (-97.05, 27.75), (-97.35, 27.30), (-97.40, 26.80), (-97.20, 26.15),
         (-97.15, 25.96), (-97.60, 25.90), (-98.25, 26.05), (-98.75, 26.20), (-99.10, 26.42), (-99.30, 26.85), (-99.45, 27.10),
         (-99.52, 27.50), (-99.85, 27.90), (-100.20, 28.20), (-100.40, 28.60), (-100.65, 29.10), (-101.05, 29.45), (-101.40, 29.77),
         (-102.00, 29.82), (-102.30, 29.88), (-102.70, 29.70), (-102.90, 29.25), (-103.15, 28.97), (-103.75, 29.25),
         (-104.20, 29.55), (-104.50, 29.70), (-104.70, 30.00), (-104.90, 30.55), (-105.00, 30.68), (-105.55, 31.08),
         (-106.05, 31.40), (-106.50, 31.75), (-106.62, 32.00), (-103.06, 32.00)]


def project(lon, lat):
    return round((lon + 106.8) * math.cos(math.radians(31.2)) * 100, 1), round((36.6 - lat) * 100, 1)


def texas_map():
    path = "M" + " L".join(f"{x},{y}" for x, y in (project(*p) for p in TEXAS)) + "Z"
    pins = []
    for i, office in enumerate(OFFICES):
        x, y = project(office["lon"], office["lat"])
        dx, dy, anchor = office["label"]
        pins.append(
            f'<g class="map__pin{" is-active" if i == 0 else ""}" data-office="{office["key"]}" role="button" tabindex="0" '
            f'aria-label="{office["name"]} office" transform="translate({x} {y})">'
            f'<circle class="hit" r="30"/><circle class="ring" r="14"/><circle class="dot" r="14"/>'
            f'<text x="{dx + (6 if dx > 0 else -6)}" y="{dy}" text-anchor="{anchor}">{office["name"]}</text></g>'
        )
    return (f'<svg viewBox="500 270 680 600" role="img" aria-label="Map of Texas showing Holden Roofing offices">'
            f'<path class="map__state" d="{path}"/>{"".join(pins)}</svg>')


def office_tabs():
    return "".join(
        f'<button class="office-tab" role="tab" type="button" data-office="{o["key"]}" aria-selected="{"true" if i == 0 else "false"}">{o["name"]}</button>'
        for i, o in enumerate(OFFICES))


def maps_query(office):
    return f'Holden Roofing, {office["street"]}, {office["city"]}'.replace(" ", "+").replace("#", "%23")


def office_panels():
    panels = []
    for i, o in enumerate(OFFICES):
        tel = re.sub(r"\D", "", o["phone"])
        meta = f'<span>{icon("star", True)} {o["meta"]}</span>' if o["meta"] else ""
        panels.append(f'''<article class="office{" is-active" if i == 0 else ""}" id="office-{o["key"]}" data-office="{o["key"]}" data-query="{maps_query(o)}" role="tabpanel">
  <div class="office__img"><img src="assets/img/{o["img"]}-800.webp" alt="{o["name"]}, Texas skyline" width="800" height="300" loading="lazy" decoding="async"><span>{o["tag"]}</span></div>
  <div class="office__body">
    <div>
      <h3>Holden Roofing {o["name"]}</h3>
      <p class="lead" style="font-size:1rem;margin:0 0 14px">{o["blurb"]}</p>
      <address>{icon("pin")}<span>{o["street"]}<br>{o["city"]}</span></address>
    </div>
    <div style="display:grid;gap:16px;align-content:start">
      <div class="office__meta"><span>{icon("phone")} <a href="tel:+1{tel}" style="font-weight:700;text-decoration:none">{o["phone"]}</a></span>{meta}</div>
      <div class="office__actions">
        <a class="btn btn--primary btn--sm" href="tel:+1{tel}">{icon("phone")} Call office</a>
        <a class="btn btn--outline btn--sm" href="https://www.google.com/maps/dir/?api=1&amp;destination={maps_query(o)}" target="_blank" rel="noopener">{icon("nav")} Directions</a>
      </div>
    </div>
    <div class="office__map" data-map></div>
  </div>
</article>''')
    return "\n".join(panels)


def office_cards():
    cards = []
    for o in OFFICES:
        tel = re.sub(r"\D", "", o["phone"])
        cards.append(f'''<article class="office-card reveal">
  <img src="assets/img/{o["img"]}-800.webp" alt="" width="800" height="400" loading="lazy" decoding="async">
  <div><h3>{o["name"]}</h3><p>{o["street"]}<br>{o["city"]}</p>
  <a class="tel" href="tel:+1{tel}">{o["phone"]}</a>
  <a class="link-arrow" href="https://www.google.com/maps/dir/?api=1&amp;destination={maps_query(o)}" target="_blank" rel="noopener">Get directions {icon("arrow")}</a></div>
</article>''')
    return "\n".join(cards)


def service_areas():
    out = []
    for title, towns in SERVICE_AREAS.items():
        chips = "".join(f'<li class="chip">{t}</li>' for t in towns)
        out.append(f'<div class="reveal"><h3 style="font-size:1.3rem">{title}</h3><ul class="chips">{chips}</ul></div>')
    return "\n".join(out)


def review_card(name, when, text):
    initials = "".join(part[0] for part in name.split()[:2]).upper()
    return (f'<article class="review"><div class="stars-row">{stars()}</div><blockquote><p>{text}</p></blockquote>'
            f'<footer><span class="avatar" aria-hidden="true">{initials}</span><div><strong>{name}</strong>'
            f'<small>Google review · {when}</small></div></footer></article>')


def reviews_carousel():
    return "\n".join(review_card(*r) for r in REVIEWS)


# ---- Layout ----------------------------------------------------------------------------------
def header(nav_key):
    items = []
    for key, label, href in NAV:
        if href:
            current = ' aria-current="page"' if key == nav_key else ""
            items.append(f'<li><a class="nav__link" href="{href}"{current}>{label}</a></li>')
        else:
            current = ' aria-current="page"' if nav_key == "roofing" else ""
            menu = "".join(
                f'<a href="{h}"><span class="ico">{icon(ic)}</span><span><strong>{t}</strong><small>{d}</small></span></a>'
                for h, t, d, ic in ROOFING_MENU)
            items.append(f'<li class="has-menu"><button class="nav__link" type="button" aria-haspopup="true"{current}>{label} {icon("chevron-down")}</button>'
                         f'<div class="menu">{menu}</div></li>')
    drawer_links = ['<a href="index.html" style="--i:0">Home</a>']
    n = 1
    for key, label, href in NAV:
        if href:
            drawer_links.append(f'<a href="{href}" style="--i:{n}">{label}</a>')
            n += 1
        else:
            drawer_links.append(f'<a href="residential-roofing.html" style="--i:{n}">Residential Roofing</a>')
            drawer_links.append(f'<a href="commercial-roofing.html" style="--i:{n + 1}">Commercial Roofing</a>')
            drawer_links.append(f'<a href="storm-damage-repair.html" style="--i:{n + 2}">Storm Damage Repair</a>')
            n += 3
    return f'''<header class="header" id="header">
  <div class="topbar"><div class="container topbar__in">
    <p>Family-owned Texas roofer · Roofing Texas homes since 1961</p>
    <div class="topbar__links"><a href="tel:{TEL}">{icon("phone")} Toll free {PHONE}</a><a href="{PAY_URL}" target="_blank" rel="noopener">{icon("dollar")} Make a Payment</a></div>
  </div></div>
  <div class="header__bar"><div class="container header__in">
    <a class="brand" href="index.html" aria-label="Holden Roofing — home"><img src="assets/img/logo-200.webp" srcset="assets/img/logo-200.webp 200w, assets/img/logo-400.webp 400w" sizes="90px" alt="Holden Roofing — set in stone since 1961" width="104" height="46"></a>
    <nav class="nav" aria-label="Primary"><ul class="nav__list">{"".join(items)}</ul></nav>
    <div class="header__actions">
      <a class="btn btn--primary btn--sm header__cta" href="contact.html">Free Roof Inspection {icon("arrow").replace('class="i"', 'class="i i-arrow"')}</a>
      <a class="icon-btn" href="tel:{TEL}" aria-label="Call Holden Roofing">{icon("phone")}</a>
      <button class="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{icon("menu")}</button>
    </div>
  </div></div>
</header>
<div class="drawer" id="drawer" aria-hidden="true">
  <div class="drawer__scrim" data-close></div>
  <div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Menu">
    <div class="drawer__top"><img src="assets/img/logo-200.webp" alt="Holden Roofing" width="90" height="40"><button class="drawer__close" type="button" aria-label="Close menu" data-close>{icon("close")}</button></div>
    <nav class="drawer__nav" aria-label="Mobile">{"".join(drawer_links)}</nav>
    <div class="drawer__foot">
      <a class="btn btn--primary btn--lg btn--block" href="contact.html">Book a Free Roof Inspection</a>
      <a class="btn btn--ghost btn--block" href="tel:{TEL}">{icon("phone")} {PHONE}</a>
      <a class="btn btn--ghost btn--block" href="{PAY_URL}" target="_blank" rel="noopener">Make a Payment</a>
      <p>7 Texas offices · Family-owned since 1961</p>
    </div>
  </div>
</div>'''


def footer():
    offices = "".join(
        f'<li><a href="locations.html#office-{o["key"]}">{o["name"]}</a><a href="tel:+1{re.sub(chr(92) + "D", "", o["phone"])}">{o["phone"]}</a></li>'
        for o in OFFICES)
    social = "".join(f'<a href="{url}" target="_blank" rel="noopener" aria-label="{label}">{icon(name)}</a>' for name, url, label in SOCIAL)
    return f'''<footer class="footer">
  <div class="container footer__grid">
    <div>
      <img class="logo" src="assets/img/logo-200.webp" srcset="assets/img/logo-200.webp 200w, assets/img/logo-400.webp 400w" sizes="130px" alt="Holden Roofing" width="130" height="58" loading="lazy">
      <p>A Texas roofing family since 1961. Residential and commercial roofing, storm damage repair, and work we stand behind.</p>
      <a class="footer__phone" href="tel:{TEL}">{PHONE}</a>
      <div class="social">{social}</div>
    </div>
    <div>
      <h4>Explore</h4>
      <ul><li><a href="residential-roofing.html">Residential Roofing</a></li><li><a href="commercial-roofing.html">Commercial Roofing</a></li><li><a href="storm-damage-repair.html">Storm Damage Repair</a></li><li><a href="financing.html">Financing</a></li><li><a href="reviews.html">Reviews</a></li><li><a href="about.html">About Us</a></li><li><a href="contact.html">Contact</a></li></ul>
    </div>
    <div>
      <h4>Company</h4>
      <ul><li><a href="{PAY_URL}" target="_blank" rel="noopener">Make a Payment</a></li><li><a href="mailto:recruiting@holdenroofing.com">Careers</a></li><li><a href="privacy.html">Privacy Policy</a></li></ul>
      <p style="margin-top:22px">Owens Corning<br>Platinum Preferred Contractor</p>
    </div>
    <div>
      <h4>Texas offices</h4>
      <ul class="footer__offices">{offices}</ul>
    </div>
  </div>
  <div class="container footer__bottom"><span>© <span data-year>2026</span> Holden Roofing. All rights reserved.</span><nav aria-label="Legal"><a href="privacy.html">Privacy Policy</a><a href="locations.html">Locations</a><a href="contact.html">Contact</a></nav></div>
</footer>
<div class="sticky-cta" id="sticky-cta"><a class="btn btn--ghost" href="tel:{TEL}">{icon("phone")} Call</a><a class="btn btn--primary" href="contact.html">Free Roof Inspection</a></div>
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer" aria-hidden="true"><button class="lb-close" type="button" aria-label="Close">{icon("close")}</button><button class="lb-prev" type="button" aria-label="Previous photo">{icon("chevron-left")}</button><figure><img alt="" src=""><figcaption></figcaption></figure><button class="lb-next" type="button" aria-label="Next photo">{icon("chevron-right")}</button></div>'''


def json_ld():
    import json
    departments = [{
        "@type": "RoofingContractor", "name": f"Holden Roofing {o['name']}", "telephone": "+1" + re.sub(r"\D", "", o["phone"]),
        "address": {"@type": "PostalAddress", "streetAddress": o["street"], "addressLocality": o["city"].split(",")[0],
                    "addressRegion": "TX", "postalCode": o["city"].split()[-1], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": o["lat"], "longitude": o["lon"]},
    } for o in OFFICES]
    data = {"@context": "https://schema.org", "@type": "RoofingContractor", "name": "Holden Roofing", "url": SITE_URL,
            "telephone": "+18885531318", "foundingDate": "1961", "image": SITE_URL + "assets/img/og.jpg",
            "logo": SITE_URL + "assets/img/logo-400.webp", "areaServed": {"@type": "State", "name": "Texas"},
            "sameAs": [s[1] for s in SOCIAL], "department": departments}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


def page(meta, body, filename):
    title, desc = meta["title"], meta["description"]
    og_image = SITE_URL + "assets/img/" + meta.get("og_image", "og.jpg")
    preload = ""
    if meta.get("preload"):
        preload = (f'<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/hero-480.webp 480w, assets/img/hero-960.webp 960w, '
                   f'assets/img/hero-1600.webp 1600w" imagesizes="100vw" fetchpriority="high">')
    ld = json_ld() if meta.get("jsonld") else ""
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    site_path = urlparse(SITE_URL).path
    base = ('<script>document.write(\'<base href="\' + (location.pathname.indexOf("' + site_path + '") === 0 ? "' + site_path
            + '" : "/") + \'">\')</script>') if meta.get("base") else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{base}
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0a1e3f">
{robots}
<link rel="canonical" href="{SITE_URL}{"" if filename == "index.html" else filename}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Holden Roofing">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{SITE_URL}{"" if filename == "index.html" else filename}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/fraunces.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
{preload}
<script>document.documentElement.classList.add("js")</script>
<link rel="stylesheet" href="assets/css/styles.css">
{ld}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{sprite()}
{header(meta.get("nav", ""))}
<main id="main">
{body}
</main>
{footer()}
<script src="assets/js/app.js" defer></script>
</body>
</html>
'''


def parse_page(text):
    match = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    meta = {}
    for line in match.group(1).strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def render(body):
    tokens = {
        "{{map}}": texas_map(), "{{office_tabs}}": office_tabs(), "{{office_panels}}": office_panels(),
        "{{office_cards}}": office_cards(), "{{service_areas}}": service_areas(), "{{reviews}}": reviews_carousel(),
        "{{estimator}}": read("partials", "estimator.html"), "{{cta}}": read("partials", "cta.html"),
        "{{locator}}": read("partials", "locator.html"),
    }
    for _ in range(2):  # partials may contain other tokens
        for token, value in tokens.items():
            body = body.replace(token, value)
    body = body.replace("{{pay_url}}", PAY_URL).replace("{{phone}}", PHONE).replace("{{tel}}", TEL)
    body = re.sub(r"\{\{stars\}\}", stars(), body)
    return expand_icons(body)


def main():
    pages_dir = os.path.join(SRC, "pages")
    urls = []
    for name in sorted(os.listdir(pages_dir)):
        if not name.endswith(".html"):
            continue
        meta, body = parse_page(read("pages", name))
        html = page(meta, render(body), name)
        with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as out:
            out.write(html)
        if not meta.get("noindex"):
            urls.append(name)
        print("built", name, len(html) // 1024, "KB")
    sitemap = "".join(f"<url><loc>{SITE_URL}{'' if u == 'index.html' else u}</loc></url>" for u in urls)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as out:
        out.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>\n')
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as out:
        out.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")


if __name__ == "__main__":
    main()
