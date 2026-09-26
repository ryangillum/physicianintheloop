#!/usr/bin/env python3
"""Build the public website for Physician in the Loop (physicianintheloop.org).

Usage:  python3 build_public_site.py <artifact.html> <repo root> [site.config.json]

<artifact.html> is the claude.ai page as saved by the Artifact tool's read action (wrapped in
claude.ai's skeleton or not; both work). The script writes a complete multi-page static site into
<repo root>/public/ (wiping it first) and netlify.toml at <repo root>. Nothing else in the repository
is touched. Content is never edited: every post, letter, special topic, watch-list entry and date is
rendered from the page's JSON exactly as it is, with one page per piece so each has its own address,
title, description and structured data for search engines.

Version 2 (Sept 24, 2026): multi-page site, RSS feed, sitemap, JSON-LD, analytics from the config file.
Version 2.1 (Sept 24, 2026): topic hub pages (/topics/<category>/), item anchors, Google News sitemap, llms.txt.
Version 2.2 (Sept 25, 2026): Friday letters open with their illustration (letter.image, a data URI written to
/images/letters/<weekOf>.<ext>) in place of THE SHORT READ label, which stays on daily posts; the image is the
letter page's social preview and structured-data image, heads the letter in the feed, and shows on the home page.
Version 2.3 (Sept 25, 2026): daily posts get the same treatment (post.image above THE SHORT READ, /images/posts/<slug>.<ext>,
the post page's social image; not added to the feed, which the podcast reads). Every illustration is also kept under
<repo root>/assets/images/, so a post or letter keeps its picture on the site after the working page retires the
picture's data (it leaves image {alt} with no src) or trims the post; that folder is the only thing outside public/
the script writes besides netlify.toml. Image addresses carry ?v=<hash> so a replaced picture is never served stale.
Version 2.4 (Sept 26, 2026): the podcast. A /podcast/ page plays every episode in Transistor's playlist player (the dark
variant when the reader's system is dark), with Apple Podcasts, Spotify and RSS links and PodcastSeries structured data;
a Podcast tab sits second in the navigation, the home page carries the latest episode's player after today's post, every
article's subscribe box has a "Listen to the podcast" button, /listen redirects to /podcast/, and the footer carries the
copyright line. The podcast and the copyright holder come from site.config.json ("podcast", "copyright_holder"; set
"podcast" to false to leave the podcast out).
"""
import sys, re, os, io, json, html as H, base64, hashlib, shutil, datetime, urllib.parse

# ------------------------------------------------------------------ inputs
if len(sys.argv) < 3:
    sys.exit(__doc__)
SRC, ROOT = sys.argv[1], sys.argv[2]
CONFIG_PATH = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "tools", "site.config.json")
OUT = os.path.join(ROOT, "public")

DEFAULT_CONFIG = {
    "site_url": "https://physicianintheloop.org/",
    "site_name": "Physician in the Loop",
    "tagline": "AI in medicine, for physicians",
    "description": "How artificial intelligence changes medicine for the people who actually practice it. Daily posts, a Friday letter, a watch list, and a calendar of the dates that matter.",
    "author": "Ryan Gillum, MD",
    "substack_url": "https://physicianintheloop.substack.com",
    "subscribe_url": "https://physicianintheloop.substack.com/subscribe",
    "timezone": "America/Denver",
    "analytics": {"provider": None, "id": None},
    "google_site_verification": None,
    "bing_verification": None,
    "twitter_handle": None,
    "copyright_holder": "Nomad Medical Group, LLC",
    "podcast": {
        "name": "Physician in the Loop",
        "transistor_slug": "physician-in-the-loop",
        "rss": "https://feeds.transistor.fm/physician-in-the-loop",
        "apple": "https://podcasts.apple.com/podcast/physician-in-the-loop/id6815879355",
        "spotify": "https://open.spotify.com/show/6F9zsXoKZGAvqPx2GmDSqh",
        "youtube": None,
        "playlist_height": 390,
    },
}
config = dict(DEFAULT_CONFIG)
if os.path.exists(CONFIG_PATH):
    try:
        user_cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
        for k, v in user_cfg.items():
            if v is not None and v != "":
                config[k] = v
    except Exception as e:  # a broken config must not stop the morning publish
        print("warning: could not read", CONFIG_PATH, "->", e, file=sys.stderr)
SITE = config["site_url"].rstrip("/") + "/"
NAME = config["site_name"]
AUTHOR = config["author"]
POD = None
if config.get("podcast") is not False:
    POD = dict(DEFAULT_CONFIG["podcast"])
    if isinstance(config.get("podcast"), dict):
        POD.update({k: v for k, v in config["podcast"].items() if v})
    if not (POD.get("transistor_slug") and POD.get("rss")):
        POD = None

# ------------------------------------------------------------------ read the artifact page
raw = open(SRC, encoding="utf-8").read()
b = raw.find("<body>")
if b != -1 and raw.find("<title>") > b:  # claude.ai skeleton: our page sits inside <body>
    raw = raw[b + len("<body>"):]
    e = raw.rfind("</body>")
    if e != -1:
        raw = raw[:e]
raw = raw.strip()

m = re.search(r"<title>(.*?)</title>", raw, re.S)
PAGE_TITLE = H.unescape(m.group(1)).strip() if m else NAME
m = re.search(r'<link rel="stylesheet"[^>]*fonts\.googleapis\.com[^>]*>', raw)
FONT_LINK = m.group(0) if m else ""
m = re.search(r"<style>(.*?)</style>", raw, re.S)
SITE_CSS = m.group(1) if m else ""
m = re.search(r'<script id="site-data" type="application/json">(.*?)</script>', raw, re.S)
if not m:
    sys.exit("site-data block not found in " + SRC)
data = json.loads(m.group(1))
meta = data.get("meta", {})
posts = data.get("posts") or []
letters = data.get("letters") or []
specials = data.get("specials") or []
watchlist = data.get("watchlist") or []
dates = data.get("dates") or []
LAST_UPDATED = meta.get("lastUpdated", "") or datetime.date.today().isoformat()
LAST_LABEL = meta.get("lastUpdatedLabel", "")
SUBSTACK = meta.get("substackUrl") or config["substack_url"]
SUBSCRIBE = meta.get("subscribeUrl") or config["subscribe_url"]

def section_html(sec_id):
    """Inner HTML of <section ... id="sec_id"> ... </section> from the artifact page."""
    m = re.search(r'<section[^>]*\bid="%s"[^>]*>(.*?)</section>' % re.escape(sec_id), raw, re.S)
    return m.group(1) if m else ""

# ------------------------------------------------------------------ helpers
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
STATUS = {"rising": "heating up", "active": "in motion", "quiet": "quiet", "favorable": "in our favor"}
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")

def esc(s):
    return H.escape("" if s is None else str(s), quote=True)

def fmt(d):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", d or "")
    if not m:
        return d or ""
    return "%s %d, %s" % (MONTHS[int(m.group(2)) - 1], int(m.group(3)), m.group(1))

def month_label(key):
    m = re.match(r"^(\d{4})-(\d{2})", key or "")
    return "%s %s" % (MONTHS_LONG[int(m.group(2)) - 1], m.group(1)) if m else "Undated"

def ext_link(text, url, cls=None):
    return '<a%s href="%s" target="_blank" rel="noopener">%s</a>' % ((' class="%s"' % cls) if cls else "", esc(url), esc(text))

def rich(text):
    """[phrase](https://url) inline links to anchors; everything else escaped."""
    text = "" if text is None else str(text)
    out, last = [], 0
    for m in LINK_RE.finditer(text):
        out.append(esc(text[last:m.start()]))
        out.append(ext_link(m.group(1), m.group(2)))
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)

def plain(text):
    return LINK_RE.sub(lambda m: m.group(1), "" if text is None else str(text)).strip()

def describe(parts, limit=158):
    """A meta description from the first paragraph(s): whole sentences where possible."""
    text = " ".join(plain(p) for p in parts if p).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    m = list(re.finditer(r"[.!?](?=\s)", cut))
    if m and m[-1].end() > limit * 0.55:
        return cut[:m[-1].end()]
    return cut[:cut.rfind(" ")].rstrip(",;:") + "..."

def sources_line(cls, srcs, fallback_label=None, fallback_url=None):
    srcs = srcs if srcs else ([{"label": fallback_label or fallback_url, "url": fallback_url}] if (fallback_label or fallback_url) else [])
    if not srcs:
        return ""
    bits = []
    for s in srcs:
        if s.get("url"):
            bits.append(ext_link(s.get("label") or s["url"], s["url"]))
        else:
            bits.append(esc(s.get("label") or ""))
    return '<div class="%s">%s%s</div>' % (cls, "Sources: " if len(srcs) > 1 else "Source: ", ", ".join(bits))

def render_items(items, anchors=False):
    if not items:
        return ""
    out = ['<ul class="items">']
    for n, it in enumerate(items, 1):
        if isinstance(it, str):
            it = {"title": it}
        cat = esc(it.get("category") or "")
        if it.get("date"):
            cat += '  <span class="when">%s</span>' % esc(fmt(it["date"]))
        title = ext_link(it.get("title") or "", it["url"]) if it.get("url") else esc(it.get("title") or "")
        out.append('<li class="item"%s><div class="cat">%s</div><div class="item-title">%s</div>' % ((' id="item-%d"' % n) if anchors else "", cat, title))
        if it.get("body"):
            out.append('<div class="item-body">%s</div>' % rich(it["body"]))
        out.append(sources_line("item-src", it.get("sources"), it.get("source"), it.get("url")))
        out.append("</li>")
    out.append("</ul>")
    return "".join(out)

def paras(arr, cls=""):
    if not arr:
        return ""
    if isinstance(arr, str):
        arr = [arr]
    return '<div class="%s">%s</div>' % (cls, "".join("<p>%s</p>" % rich(t) for t in arr if t))

def post_body(p, anchors=False, fig=""):
    out = [fig] if fig else []
    intro = p.get("intro") or p.get("summary")
    if intro:
        out.append('<div class="section-label">THE SHORT READ</div>')
        out.append(paras(intro, "intro"))
    if p.get("items"):
        out.append('<div class="section-label details-label">THE DETAILS</div>')
        out.append(render_items(p["items"], anchors))
    return "".join(out)

# ------------------------------------------------------------------ dates and times
def tz_offset(date_str):
    """Offset string (-06:00 / -07:00) for 7 AM local on that date in the site's time zone."""
    try:
        from zoneinfo import ZoneInfo
        y, mo, d = (int(x) for x in date_str[:10].split("-"))
        dt = datetime.datetime(y, mo, d, 7, 0, tzinfo=ZoneInfo(config["timezone"]))
        off = dt.utcoffset()
        secs = int(off.total_seconds())
        sign = "-" if secs < 0 else "+"
        secs = abs(secs)
        return "%s%02d:%02d" % (sign, secs // 3600, (secs % 3600) // 60)
    except Exception:
        return "-06:00"

def iso_dt(date_str):
    date_str = (date_str or LAST_UPDATED)[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_str = LAST_UPDATED
    return "%sT07:00:00%s" % (date_str, tz_offset(date_str))

def rfc822(date_str):
    date_str = (date_str or LAST_UPDATED)[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_str = LAST_UPDATED
    y, mo, d = (int(x) for x in date_str.split("-"))
    dt = datetime.date(y, mo, d)
    off = tz_offset(date_str).replace(":", "")
    return "%s, %02d %s %d 07:00:00 %s" % (["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()], d, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][mo - 1], y, off)

# ------------------------------------------------------------------ slugs and urls
def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "item"

used_slugs = set()
def unique(slug):
    base, n = slug, 2
    while slug in used_slugs:
        slug = "%s-%d" % (base, n); n += 1
    used_slugs.add(slug)
    return slug

post_pages = []   # (slug, post)
for p in posts:
    s = (p.get("date") or "undated") + ("-launch" if p.get("baseline") else "")
    post_pages.append((unique("post:" + s)[5:], p))
used_slugs = set()
letter_pages = [(unique((w.get("weekOf") or "week-%d" % i)), w) for i, w in enumerate(letters)]
used_slugs = set()
special_pages = [(unique(sp.get("slug") or slugify(sp.get("title")) or "special-%d" % i), sp) for i, sp in enumerate(specials)]

def post_url(slug): return "/posts/%s/" % slug
def letter_url(slug): return "/letters/%s/" % slug
def special_url(slug): return "/specials/%s/" % slug
def absurl(path): return SITE.rstrip("/") + path

NAV = [("/", "Today")] + ([("/podcast/", "Podcast")] if POD else []) + [("/posts/", "Daily posts"), ("/letters/", "Friday letter"), ("/specials/", "Special topics"),
       ("/watch/", "Watch list"), ("/dates/", "Dates"), ("/where-things-stand/", "Where things stand"), ("/about/", "About")]
HASH_MAP = {"today": "/", "podcast": "/podcast/", "posts": "/posts/", "letters": "/letters/", "specials": "/specials/", "watch": "/watch/", "dates": "/dates/", "landscape": "/where-things-stand/", "about": "/about/"}
ICON = ('<svg class="ico" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
        '<path d="M4 15v-3a8 8 0 0 1 16 0v3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
        '<rect x="3" y="13" width="5" height="8" rx="2" fill="currentColor"/><rect x="16" y="13" width="5" height="8" rx="2" fill="currentColor"/></svg>')
TAB_ICON = ICON.replace('class="ico"', 'class="tab-ico"').replace('width="18" height="18"', 'width="14" height="14"')

def fix_internal_links(fragment):
    """Turn the app's hash-tab links into real page links inside copied HTML (long read, about, masthead)."""
    def sub(m):
        return 'href="%s"' % HASH_MAP[m.group(1)]
    fragment = re.sub(r'href="#(today|podcast|posts|letters|specials|watch|dates|landscape|about)"', sub, fragment)
    fragment = re.sub(r'\s+data-tab-link="[^"]*"', "", fragment)
    fragment = re.sub(r'\s+data-scroll-top="[^"]*"', "", fragment)
    return fragment

# ------------------------------------------------------------------ page shell
EXTRA_CSS = """
  .tab { text-decoration: none; }
  .letter-art { margin: 18px 0 20px; }
  .post-art { margin: 18px 0 0; }
  .post-art + .section-label { margin-top: 24px; }
  .letter-art img, .letter-card img, .post-art img { display: block; width: 100%; height: auto; aspect-ratio: 1200 / 630; object-fit: cover; border-radius: 12px; border: 1px solid var(--rule); box-shadow: var(--shadow); background: var(--bg-2); }
  .letter .letter-art + .body-copy { margin-top: 0; }
  .letter-card { display: block; margin: 8px 0 6px; }
  .tab[aria-current="page"] { color: var(--accent-ink); background: var(--accent); }
  .tab[aria-current="page"] .n { background: rgba(255,255,255,0.22); color: var(--accent-ink); }
  main { display: block; }
  .post h1.headline { font-size: clamp(1.55rem, 4.6vw, 2.15rem); margin-top: 8px; line-height: 1.15; letter-spacing: -0.01em; }
  .post .standfirst { font-family: var(--display); font-size: 1.15rem; color: var(--ink-2); margin-top: 10px; line-height: 1.45; }
  .post .body-copy { margin-top: 14px; }
  .post .section-label + .body-copy { margin-top: 12px; }
  .post .outlook .section-label + div { margin-top: 12px; }
  .post .special-body { margin-top: 6px; }
  .crumbs { font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); margin: 18px 0 12px; }
  .crumbs a { color: var(--muted); text-decoration: none; }
  .crumbs a:hover { color: var(--accent-2); }
  .archive { list-style: none; margin: 8px 0 0; padding: 0; }
  .archive li { padding-block: 12px; border-top: 1px solid var(--rule); display: grid; grid-template-columns: 96px 1fr; gap: 4px 14px; }
  .archive li:last-child { border-bottom: 1px solid var(--rule); }
  .archive .when { font-family: var(--mono); font-size: 0.72rem; color: var(--muted); padding-top: 5px; }
  .archive a { font-family: var(--display); font-weight: 600; font-size: 1.08rem; line-height: 1.3; color: var(--ink); text-decoration: none; }
  .archive a:hover { color: var(--accent-2); }
  .archive .d { grid-column: 2; font-size: 0.95rem; color: var(--muted); }
  @media (max-width: 480px) { .archive li { grid-template-columns: 1fr; } .archive .d { grid-column: 1; } }
  .pager { display: flex; justify-content: space-between; gap: 16px; margin-top: 26px; padding-top: 18px; border-top: 1px solid var(--rule); font-size: 0.95rem; }
  .pager a { font-weight: 600; text-decoration: none; max-width: 48%; }
  .pager a:hover { text-decoration: underline; }
  .pager .lbl { display: block; font-family: var(--mono); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 3px; }
  .subscribe-box { margin-top: 28px; padding: 20px 22px; background: var(--accent-soft); border-radius: 12px; }
  .subscribe-box p { margin: 0 0 12px; color: var(--ink-2); }
  .doc .doc-title { font-size: clamp(1.6rem, 4.6vw, 2rem); margin: 4px 0 14px; line-height: 1.15; }
  .foot .tablinks { display: flex; flex-wrap: wrap; gap: 4px 0; }
  .btn.listen { display: inline-flex; align-items: center; gap: 8px; background: var(--ink); color: var(--bg); }
  .btn.listen:hover { background: var(--accent-2); color: var(--accent-ink); }
  .btn .ico { width: 18px; height: 18px; flex: 0 0 auto; }
  .tab .tab-ico { width: 14px; height: 14px; margin-right: 6px; vertical-align: -2px; }
  .pod-apps { display: flex; flex-wrap: wrap; gap: 10px; }
  .pod-feed { font-size: 0.9rem; color: var(--muted); margin: 14px 0 0; overflow-wrap: anywhere; }
  .pod-feed code { font-family: var(--mono); font-size: 0.8rem; color: var(--ink-2); user-select: all; }
  .pod-player { border-radius: 12px; overflow: hidden; border: 1px solid var(--rule); box-shadow: var(--shadow); background: var(--surface); }
  .pod-player iframe { display: block; width: 100%; border: 0; }
  .pod-player + .pod-apps { margin-top: 12px; }
  .pod-follow { font-size: 1.3rem; margin: 30px 0 12px; }
  .subscribe-actions { display: flex; flex-wrap: wrap; gap: 10px; }
  .copyright { margin-top: 6px; font-size: 0.8rem; }
"""

def analytics_snippet():
    a = config.get("analytics") or {}
    provider, ident = (a.get("provider") or "").lower(), (a.get("id") or "").strip()
    if not provider or not ident:
        return ""
    if provider in ("ga4", "google", "gtag"):
        return ('<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>'
                '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","%s");</script>' % (esc(ident), esc(ident)))
    if provider == "plausible":
        return '<script defer data-domain="%s" src="https://plausible.io/js/script.outbound-links.js"></script>' % esc(ident)
    if provider == "cloudflare":
        return "<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{\"token\": \"%s\"}'></script>" % esc(ident)
    if provider == "umami":
        # id = "<script src>|<website-id>" or just the website id on cloud.umami.is
        src, _, wid = ident.partition("|")
        if not wid:
            src, wid = "https://cloud.umami.is/script.js", src
        return '<script defer src="%s" data-website-id="%s"></script>' % (esc(src), esc(wid))
    if provider == "fathom":
        return '<script src="https://cdn.usefathom.com/script.js" data-site="%s" defer></script>' % esc(ident)
    return ""

ANALYTICS = analytics_snippet()

def nav_html(active):
    out = ['<div class="topbar" id="topbar"><div class="topbar-inner"><div class="brand-row">',
           '<a class="brand" href="/">%s</a>' % esc(NAME),
           '<a class="btn small" href="%s" target="_blank" rel="noopener">Subscribe</a></div>' % esc(SUBSCRIBE),
           '<nav class="tabs" aria-label="Sections">']
    for path, label in NAV:
        cur = ' aria-current="page"' if path == active else ""
        count = '<span class="n">%d</span>' % len(posts) if (path == "/posts/" and posts) else ""
        out.append('<a class="tab" href="%s"%s>%s%s%s</a>' % (path, cur, TAB_ICON if path == "/podcast/" else "", esc(label), count))
    out.append("</nav></div></div>")
    return "".join(out)

FOOT = ('<footer class="foot"><div class="tablinks">' + "".join('<a href="%s">%s</a>' % (p, esc(l)) for p, l in NAV) +
        '</div><p style="margin-top:10px">%s. Written by %s. Daily on this site, weekly on <a href="%s" target="_blank" rel="noopener">Substack</a>. '
        'Not medical, legal, or financial advice. <a href="/topics/">Topics</a>. <a href="/feed.xml">RSS</a>.</p>'
        '<p class="copyright">&copy; %d %s. All rights reserved.</p></footer>' % (esc(NAME), esc(AUTHOR), esc(SUBSTACK), datetime.date.today().year, esc(config.get("copyright_holder") or AUTHOR)))

def page(path, title, desc, body, active=None, kind="website", jsonld=None, published=None, modified=None, head_extra="", image=None, image_alt=None):
    url = absurl(path)
    og_img = (absurl(image) if image.startswith("/") else image) if image else absurl("/og-image.png")
    full_title = title if (title.startswith(NAME) or title.endswith(NAME)) else "%s | %s" % (title, NAME)
    head = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            '<title>%s</title>' % esc(full_title),
            '<meta name="description" content="%s">' % esc(desc),
            '<meta name="author" content="%s">' % esc(AUTHOR),
            '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">',
            '<link rel="canonical" href="%s">' % esc(url),
            '<meta property="og:type" content="%s">' % esc(kind),
            '<meta property="og:site_name" content="%s">' % esc(NAME),
            '<meta property="og:title" content="%s">' % esc(title),
            '<meta property="og:description" content="%s">' % esc(desc),
            '<meta property="og:url" content="%s">' % esc(url),
            '<meta property="og:image" content="%s">' % esc(og_img),
            '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
            '<meta property="og:locale" content="en_US">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:title" content="%s">' % esc(title),
            '<meta name="twitter:description" content="%s">' % esc(desc),
            '<meta name="twitter:image" content="%s">' % esc(og_img)]
    if image_alt:
        head += ['<meta property="og:image:alt" content="%s">' % esc(image_alt), '<meta name="twitter:image:alt" content="%s">' % esc(image_alt)]
    if config.get("twitter_handle"):
        head.append('<meta name="twitter:site" content="%s">' % esc(config["twitter_handle"]))
    if published:
        head.append('<meta property="article:published_time" content="%s">' % esc(published))
        head.append('<meta property="article:author" content="%s">' % esc(absurl("/about/")))
    if modified:
        head.append('<meta property="article:modified_time" content="%s">' % esc(modified))
    if config.get("google_site_verification"):
        head.append('<meta name="google-site-verification" content="%s">' % esc(config["google_site_verification"]))
    if config.get("bing_verification"):
        head.append('<meta name="msvalidate.01" content="%s">' % esc(config["bing_verification"]))
    head += ['<meta name="theme-color" content="#F5F8FC" media="(prefers-color-scheme: light)">',
             '<meta name="theme-color" content="#0F1522" media="(prefers-color-scheme: dark)">',
             '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
             '<link rel="apple-touch-icon" href="/logo.png">',
             '<link rel="alternate" type="application/rss+xml" title="%s" href="%s">' % (esc(NAME), esc(absurl("/feed.xml"))),
             '<link rel="preconnect" href="https://fonts.googleapis.com">',
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
             FONT_LINK,
             '<style>%s%s</style>' % (SITE_CSS, EXTRA_CSS)]
    if jsonld:
        for obj in (jsonld if isinstance(jsonld, list) else [jsonld]):
            head.append('<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False).replace("</", "<\\/"))
    if ANALYTICS:
        head.append(ANALYTICS)
    if head_extra:
        head.append(head_extra)
    head.append("</head>")
    doc = "\n".join(head) + "\n<body>\n" + nav_html(active) + '\n<div class="wrap">\n<main>\n' + body + "\n</main>\n" + FOOT + "\n</div>\n</body>\n</html>\n"
    write(path.rstrip("/") + "/index.html" if path.endswith("/") else path, doc)
    return url

def write(path, content, binary=False):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f:
        f.write(content)

PUBLISHER = {"@type": "Organization", "name": NAME, "url": SITE, "logo": {"@type": "ImageObject", "url": absurl("/logo.png"), "width": 512, "height": 512}}
PERSON = {"@type": "Person", "name": AUTHOR, "url": absurl("/about/"), "jobTitle": "Physician", "sameAs": [SUBSTACK]}

def article_ld(kind, url, headline, desc, date, image=None):
    return {"@context": "https://schema.org", "@type": kind, "headline": headline[:110], "description": desc,
            "datePublished": iso_dt(date), "dateModified": iso_dt(date if date != LAST_UPDATED else LAST_UPDATED),
            "author": PERSON, "publisher": PUBLISHER, "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "image": [(absurl(image) if image.startswith("/") else image) if image else absurl("/og-image.png")], "isAccessibleForFree": True, "inLanguage": "en-US"}

def breadcrumbs(items):
    """items: [(label, path)] ending with the current page (path may be None)."""
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": label, **({"item": absurl(path)} if path else {})} for i, (label, path) in enumerate(items)]}
    html_ = '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(('<a href="%s">%s</a>' % (p, esc(l))) if p else '<span>%s</span>' % esc(l) for l, p in items) + "</nav>"
    return ld, html_

def subscribe_box():
    pod = ('<a class="btn listen" href="/podcast/">%sListen to the podcast</a>' % ICON) if POD else ""
    return ('<div class="subscribe-box"><p>The Friday letter: the week that mattered and specific recommendations, free, in your inbox.</p>'
            '<div class="subscribe-actions"><a class="btn" href="%s" target="_blank" rel="noopener">Get the Friday letter</a>%s</div></div>' % (esc(SUBSCRIBE), pod))

POD_BLURB = "Each morning's post as a short two-voice audio briefing, published every day."
POD_SCRIPT = ('<script>(function(){var d=false;try{d=window.matchMedia("(prefers-color-scheme: dark)").matches}catch(e){}'
              'var f=document.querySelectorAll("iframe.pod-frame");for(var i=0;i<f.length;i++){f[i].src=f[i].getAttribute(d?"data-dark":"data-light")}})();</script>')

def pod_embed(kind, height, title, lazy=False):
    """Transistor's player: kind 'latest' (one episode) or 'playlist' (every episode). The script picks the light or dark variant."""
    base = "https://share.transistor.fm/e/%s/%s" % (POD["transistor_slug"], kind)
    return ('<div class="pod-player"><iframe class="pod-frame" data-light="%s" data-dark="%s/dark" title="%s" height="%d" scrolling="no"%s></iframe>'
            '<noscript><iframe src="%s" title="%s" height="%d" scrolling="no"></iframe></noscript></div>'
            % (esc(base), esc(base), esc(title), height, ' loading="lazy"' if lazy else "", esc(base), esc(title), height))

def pod_apps():
    links = [(label, POD.get(key)) for label, key in (("Apple Podcasts", "apple"), ("Spotify", "spotify"), ("YouTube", "youtube")) if POD.get(key)]
    return '<div class="pod-apps">%s</div>' % "".join('<a class="btn ghost small" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), esc(l)) for l, u in links)

def podcast_home():
    if not POD:
        return ""
    return ('<div class="panel-head" style="margin-top:34px"><h2 style="font-size:1.3rem">The daily podcast</h2><a class="sub" href="/podcast/">all episodes</a></div>'
            '<p class="lead" style="margin-bottom:14px">%s</p>' % esc(POD_BLURB)
            + pod_embed("latest", 180, "Latest episode of the %s podcast" % POD["name"], lazy=True) + pod_apps() + POD_SCRIPT)

def pager(prev_, next_):
    """prev_/next_ are (label, path) for the older and newer piece, or None."""
    if not prev_ and not next_:
        return ""
    left = '<a href="%s"><span class="lbl">Newer</span>%s</a>' % (next_[1], esc(next_[0])) if next_ else "<span></span>"
    right = '<a href="%s" style="text-align:right"><span class="lbl">Older</span>%s</a>' % (prev_[1], esc(prev_[0])) if prev_ else "<span></span>"
    return '<nav class="pager" aria-label="More">%s%s</nav>' % (left, right)

# ------------------------------------------------------------------ start clean
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
urls = []  # (path, lastmod, changefreq, priority)

# ------------------------------------------------------------------ about photo (data URI -> file)
about_inner = section_html("about")
photo_path = None
m = re.search(r'src="data:image/(jpeg|jpg|png|webp);base64,([^"]+)"', about_inner)
if m:
    ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
    photo_path = "/images/ryan-gillum.%s" % ext
    write(photo_path, base64.b64decode(m.group(2)), binary=True)
    about_inner = about_inner[:m.start()] + 'src="%s"' % photo_path + about_inner[m.end():]
about_inner = re.sub(r'<div class="panel-head">.*?</div>\s*', "", about_inner, count=1, flags=re.S)
about_inner = fix_internal_links(about_inner)

# ------------------------------------------------------------------ illustrations (data URI -> file, with a permanent archive)
ARCHIVE = os.path.join(ROOT, "assets", "images")
EXT = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp", "svg+xml": "svg"}

def collect_images(kind, pages):
    """kind: 'posts' or 'letters'. Returns slug -> (site path or https url, alt, raster?).

    A piece shows a picture only when its JSON has an "image" entry. An entry with a data URI is written to the
    archive (replacing any earlier picture for that slug) and served from /images/<kind>/; an entry with alt text
    but no src is one the working page has retired to stay light, and is served from the archive. A piece with no
    entry gets no picture, even if the archive holds one from an earlier version of it. The site path carries
    ?v=<hash of the file> so a replaced picture is never served from a browser's cache."""
    found = {}
    arch = os.path.join(ARCHIVE, kind)
    for slug, obj in pages:
        im = obj.get("image")
        if isinstance(im, str):
            im = {"src": im}
        if not isinstance(im, dict):
            continue
        src, alt = str(im.get("src") or ""), str(im.get("alt") or "")
        if src.startswith("https://"):
            found[slug] = (src, alt, True)
            continue
        mm = re.match(r'data:image/(jpeg|jpg|png|webp|svg\+xml);base64,(.+)$', src, re.S)
        if mm:
            try:
                raw = base64.b64decode(re.sub(r"\s+", "", mm.group(2)), validate=True)
            except Exception:
                raw = b""
            if len(raw) < 100:
                print("warning: the image data for %s/%s is not valid base64; the piece is built without a picture" % (kind, slug))
                continue
            os.makedirs(arch, exist_ok=True)
            for old in os.listdir(arch):
                if old.startswith(slug + ".") and not old.endswith(".json"):
                    os.remove(os.path.join(arch, old))
            with open(os.path.join(arch, "%s.%s" % (slug, EXT[mm.group(1)])), "wb") as f:
                f.write(raw)
            with open(os.path.join(arch, slug + ".json"), "w", encoding="utf-8") as f:
                json.dump({"alt": alt}, f, ensure_ascii=False)
        files = sorted(f for f in (os.listdir(arch) if os.path.isdir(arch) else []) if f.startswith(slug + ".") and not f.endswith(".json"))
        if not files:
            continue
        fn = files[0]
        with open(os.path.join(arch, fn), "rb") as f:
            blob = f.read()
        write("/images/%s/%s" % (kind, fn), blob, binary=True)
        if not alt:
            try:
                alt = json.load(open(os.path.join(arch, slug + ".json"), encoding="utf-8")).get("alt", "")
            except Exception:
                alt = ""
        found[slug] = ("/images/%s/%s?v=%s" % (kind, fn, hashlib.sha1(blob).hexdigest()[:10]), alt, not fn.endswith(".svg"))
    return found

LETTER_IMG = collect_images("letters", letter_pages)
POST_IMG = collect_images("posts", post_pages)

def figure_html(img_map, slug, cls, lazy=False):
    if slug not in img_map:
        return ""
    src, alt, _ = img_map[slug]
    return '<figure class="%s"><img src="%s" alt="%s" width="1200" height="630" decoding="async"%s></figure>' % (cls, esc(src), esc(alt), ' loading="lazy"' if lazy else "")

def letter_figure(slug, lazy=False):
    return figure_html(LETTER_IMG, slug, "letter-art", lazy)

def post_figure(slug, lazy=False):
    return figure_html(POST_IMG, slug, "post-art", lazy)

def og_for(img_map, slug):
    if slug in img_map and img_map[slug][2]:
        return img_map[slug][0], img_map[slug][1]
    return None, None

def letter_og(slug):
    return og_for(LETTER_IMG, slug)

# ------------------------------------------------------------------ home
masthead = re.search(r'<header class="masthead">.*?</header>', section_html("today"), re.S)
masthead = masthead.group(0) if masthead else ('<header class="masthead"><div class="eyebrow">%s</div><h1>%s</h1><p class="dek">%s</p></header>' % (esc(config["tagline"]), esc(NAME), esc(config["description"])))
masthead = re.sub(r'(<span class="who" id="last-updated">).*?(</span>)', lambda mm: mm.group(1) + esc(LAST_LABEL or fmt(LAST_UPDATED)) + mm.group(2), masthead, flags=re.S)
masthead = fix_internal_links(masthead)

body = [masthead]
if posts:
    slug0, p0 = post_pages[0]
    body.append('<div class="eyebrow">Today\'s post</div>')
    body.append('<article class="post"><div class="post-date"><time datetime="%s">%s</time></div><h2 class="headline"><a href="%s" style="color:inherit;text-decoration:none">%s</a></h2>' % (esc(p0.get("date", "")), esc(fmt(p0.get("date"))), post_url(slug0), esc(p0.get("headline", ""))))
    body.append(post_body(p0, fig=post_figure(slug0)))
    body.append('<div class="more-row"><a class="btn ghost small" href="%s">Link to this post</a><a class="btn ghost small" href="/posts/">All posts</a><a class="btn ghost small" href="/where-things-stand/">Where things stand</a>%s</div></article>'
                % (post_url(slug0), '<a class="btn ghost small" href="/specials/">Special topics</a>' if specials else ""))
    body.append(podcast_home())
    if len(post_pages) > 1:
        body.append('<div class="panel-head" style="margin-top:34px"><h2 style="font-size:1.3rem">Recent posts</h2><a class="sub" href="/posts/">all posts</a></div><ul class="recent">')
        for slug, p in post_pages[1:7]:
            body.append('<li><span class="when">%s</span><a href="%s">%s</a></li>' % (esc(fmt(p.get("date"))), post_url(slug), esc(p.get("headline", ""))))
        body.append("</ul>")
else:
    body.append('<p class="empty">No posts yet.</p>')
    body.append(podcast_home())
if letters:
    ls, w0 = letter_pages[0]
    body.append('<div class="panel-head" style="margin-top:34px"><h2 style="font-size:1.3rem">The Friday letter</h2><a class="sub" href="/letters/">all letters</a></div>')
    if ls in LETTER_IMG:
        body.append('<a class="letter-card" href="%s"><img src="%s" alt="%s" width="1200" height="630" loading="lazy" decoding="async"></a>' % (letter_url(ls), esc(LETTER_IMG[ls][0]), esc(LETTER_IMG[ls][1])))
    body.append('<ul class="recent"><li><span class="when">%s</span><a href="%s">%s</a></li></ul>' % (esc(w0.get("dateRange") or fmt(w0.get("weekOf"))), letter_url(ls), esc(w0.get("headline") or "The Friday letter")))
home_ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE, "description": config["description"], "inLanguage": "en-US", "author": PERSON, "publisher": PUBLISHER},
           {"@context": "https://schema.org", "@type": "Person", "name": AUTHOR, "url": absurl("/about/"), "jobTitle": "Physician", "sameAs": [SUBSTACK], **({"image": absurl(photo_path)} if photo_path else {})}]
HASH_REDIRECT = ('<script>(function(){var h=location.hash.replace(/^#/,"");if(!h)return;var map=%s;if(map[h]){location.replace(map[h]);return;}'
                 'var m=/^post-(\\d{4}-\\d{2}-\\d{2})-\\d+$/.exec(h);if(m){location.replace("/posts/"+m[1]+"/");return;}'
                 'if(h.indexOf("letter-")===0){location.replace("/letters/"+h.slice(7)+"/");return;}'
                 'if(h.indexOf("special-")===0){location.replace("/specials/"+h.slice(8)+"/");}})();</script>' % json.dumps(HASH_MAP))
page("/", PAGE_TITLE + ": " + config["tagline"], config["description"], '<section class="panel">' + "".join(body) + "</section>", active="/", jsonld=home_ld, head_extra=HASH_REDIRECT)
urls.append(("/", LAST_UPDATED, "daily", "1.0"))

# ------------------------------------------------------------------ daily posts
def entry_page(kind, path, crumbs, headline, desc, date, article_html, older, newer, extra_ld=None, image=None, image_alt=None):
    ld, crumb_html = breadcrumbs(crumbs)
    lds = [article_ld(kind, absurl(path), headline, desc, date, image), ld] + ([extra_ld] if extra_ld else [])
    body = crumb_html + article_html + pager(older, newer) + subscribe_box()
    page(path, headline, desc, '<section class="panel">' + body + "</section>", active="/%s/" % path.split("/")[1], kind="article", jsonld=lds, published=iso_dt(date), modified=iso_dt(date), image=image, image_alt=image_alt)

for i, (slug, p) in enumerate(post_pages):
    path = post_url(slug)
    headline = p.get("headline") or "Daily post, " + fmt(p.get("date"))
    desc = describe(p.get("intro") or p.get("summary") or [p.get("dek") or headline])
    art = ['<article class="post"><div class="post-date"><time datetime="%s">%s</time>%s</div><h1 class="headline">%s</h1>' % (esc(p.get("date", "")), esc(fmt(p.get("date"))), " · Pinned" if p.get("baseline") else "", esc(headline))]
    art.append(post_body(p, anchors=True, fig=post_figure(slug)))
    art.append("</article>")
    older = (post_pages[i + 1][1].get("headline", ""), post_url(post_pages[i + 1][0])) if i + 1 < len(post_pages) else None
    newer = (post_pages[i - 1][1].get("headline", ""), post_url(post_pages[i - 1][0])) if i > 0 else None
    og_i, og_alt = og_for(POST_IMG, slug)
    entry_page("NewsArticle", path, [(NAME, "/"), ("Daily posts", "/posts/"), (fmt(p.get("date")), None)], headline, desc, p.get("date"), "".join(art), older, newer, image=og_i, image_alt=og_alt)
    urls.append((path, p.get("date") or LAST_UPDATED, "weekly" if i else "daily", "0.8" if i < 7 else "0.6"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Daily posts</h1><span class="sub">newest first</span></div>',
        '<p class="lead">One post every morning: what happened in AI and medicine the day before, written as straight news with every source linked.</p>']
if post_pages:
    body.append('<ul class="archive">')
    for slug, p in post_pages:
        body.append('<li><span class="when">%s</span><a href="%s">%s%s</a></li>' % (esc(fmt(p.get("date"))), post_url(slug), "Pinned. " if p.get("baseline") else "", esc(p.get("headline", ""))))
    body.append("</ul>")
else:
    body.append('<p class="empty">No posts yet.</p>')
body.append('<p class="lead" style="margin-top:22px">The same items sorted by kind: <a href="/topics/regulation/">regulation</a>, <a href="/topics/deployment/">deployment</a>, <a href="/topics/evidence/">evidence</a>, <a href="/topics/money/">money</a>, <a href="/topics/workforce/">workforce</a>, <a href="/topics/incident/">incidents</a>.</p>')
page("/posts/", "Daily posts", "Every daily post from %s, newest first: AI in medicine as straight news, with the sources linked." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/posts/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Daily posts", "url": absurl("/posts/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/posts/", LAST_UPDATED, "daily", "0.9"))

# ------------------------------------------------------------------ Friday letters
for i, (slug, w) in enumerate(letter_pages):
    path = letter_url(slug)
    headline = w.get("headline") or "The Friday letter, " + (w.get("dateRange") or fmt(w.get("weekOf")))
    desc = describe([w.get("dek")] if w.get("dek") else (w.get("body") or [headline]))
    art = ['<article class="post letter"><div class="post-date">The Friday letter · <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(w.get("weekOf", "")), esc(w.get("dateRange") or fmt(w.get("weekOf"))), esc(headline))]
    if w.get("dek"):
        art.append('<p class="standfirst">%s</p>' % rich(w["dek"]))
    art.append(letter_figure(slug))
    copy = w.get("body") or w.get("summary")
    if copy:
        art.append(paras(copy, "body-copy"))
    for t in w.get("themes") or []:
        art.append("<h4>%s</h4><p>%s</p>" % (esc(t.get("title", "")), rich(t.get("body", ""))))
    if w.get("top"):
        art.append('<div class="section-label details-label">SOURCE MATERIAL</div>' + render_items(w["top"]))
    if w.get("outlook"):
        art.append('<div class="outlook"><div class="section-label details-label">LOOKING AHEAD</div>' + paras(w["outlook"]) + "</div>")
    if w.get("actions"):
        art.append('<div class="takeaway"><h4>Recommendations</h4>' + "".join("<p>%s</p>" % rich(t) for t in w["actions"]) + "</div>")
    if w.get("substackUrl"):
        art.append('<p class="mono" style="margin-top:18px">%s</p>' % ext_link("Read this letter on Substack", w["substackUrl"]))
    art.append("</article>")
    older = (letter_pages[i + 1][1].get("headline", ""), letter_url(letter_pages[i + 1][0])) if i + 1 < len(letter_pages) else None
    newer = (letter_pages[i - 1][1].get("headline", ""), letter_url(letter_pages[i - 1][0])) if i > 0 else None
    og_i, og_alt = letter_og(slug)
    entry_page("Article", path, [(NAME, "/"), ("Friday letter", "/letters/"), (w.get("dateRange") or fmt(w.get("weekOf")), None)], headline, desc, w.get("weekOf"), "".join(art), older, newer, image=og_i, image_alt=og_alt)
    urls.append((path, w.get("weekOf") or LAST_UPDATED, "monthly", "0.8"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">The Friday letter</h1><a class="sub" href="%s" target="_blank" rel="noopener">archive on Substack</a></div>' % esc(SUBSTACK),
        '<p class="lead">Once a week, the version worth keeping: the week\'s developments, why they matter, and specific recommendations. It goes to subscribers by email on Friday mornings and lands here the same day.</p>']
if letter_pages:
    body.append('<ul class="archive">')
    for slug, w in letter_pages:
        body.append('<li><span class="when">%s</span><a href="%s">%s</a>%s</li>' % (esc(w.get("dateRange") or fmt(w.get("weekOf"))), letter_url(slug), esc(w.get("headline") or "The Friday letter"), ('<span class="d">%s</span>' % esc(plain(w["dek"]))) if w.get("dek") else ""))
    body.append("</ul>")
else:
    body.append('<p class="empty">The first letter is on its way.</p>')
body.append(subscribe_box())
page("/letters/", "The Friday letter", "The weekly letter from %s: the week's developments in AI and medicine, why they matter, and specific recommendations for physicians." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/letters/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "The Friday letter", "url": absurl("/letters/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/letters/", LAST_UPDATED, "weekly", "0.9"))

# ------------------------------------------------------------------ special topics
for i, (slug, sp) in enumerate(special_pages):
    path = special_url(slug)
    title = sp.get("title") or "Special topic"
    desc = describe([sp.get("dek")] if sp.get("dek") else [b.get("text", "") for b in (sp.get("blocks") or []) if b.get("type") == "p"][:1] or [title])
    art = ['<article class="post special"><div class="post-date">Special topic · <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(sp.get("date", "")), esc(fmt(sp.get("date"))), esc(title))]
    if sp.get("dek"):
        art.append('<p class="standfirst">%s</p>' % rich(sp["dek"]))
    art.append('<div class="special-body">')
    for blk in sp.get("blocks") or []:
        t = blk.get("type")
        if t == "h":
            art.append("<h2 style=\"font-family:var(--display);font-size:1.32rem;font-weight:600;margin:30px 0 10px\">%s</h2>" % esc(blk.get("text", "")))
        elif t == "pull":
            art.append('<div class="pull">%s</div>' % esc(blk.get("text", "")))
        elif t == "step":
            art.append('<p class="step"><strong>%s</strong> %s</p>' % (esc(blk.get("lead", "")), rich(blk.get("text", ""))))
        else:
            art.append("<p>%s</p>" % rich(blk.get("text", "")))
    art.append("</div>")
    if sp.get("substackUrl"):
        art.append('<p class="mono" style="margin-top:18px">%s</p>' % ext_link("Read this on Substack", sp["substackUrl"]))
    art.append("</article>")
    older = (special_pages[i + 1][1].get("title", ""), special_url(special_pages[i + 1][0])) if i + 1 < len(special_pages) else None
    newer = (special_pages[i - 1][1].get("title", ""), special_url(special_pages[i - 1][0])) if i > 0 else None
    entry_page("Article", path, [(NAME, "/"), ("Special topics", "/specials/"), (title, None)], title, desc, sp.get("date"), "".join(art), older, newer)
    urls.append((path, sp.get("date") or LAST_UPDATED, "monthly", "0.8"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Special topics</h1><span class="sub">one question, worked all the way through</span></div>',
        '<p class="lead">Longer pieces on a single question physicians keep asking, with the evidence, the rules, the prices, and a step-by-step path at the end. Each one also goes out on Substack.</p>']
if special_pages:
    body.append('<ul class="archive">')
    for slug, sp in special_pages:
        body.append('<li><span class="when">%s</span><a href="%s">%s</a>%s</li>' % (esc(fmt(sp.get("date"))), special_url(slug), esc(sp.get("title") or "Special topic"), ('<span class="d">%s</span>' % esc(plain(sp["dek"]))) if sp.get("dek") else ""))
    body.append("</ul>")
else:
    body.append('<p class="empty">The first special topic is on its way.</p>')
page("/specials/", "Special topics", "Long pieces from %s on the questions physicians keep asking about AI, with the evidence, the rules and a step-by-step path." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/specials/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Special topics", "url": absurl("/specials/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/specials/", LAST_UPDATED, "weekly", "0.8"))

# ------------------------------------------------------------------ topics (one hub page per item category)
CATEGORIES = [("regulation", "Regulation", "Regulators, payers and courts: FDA, CMS and Medicare, HHS, Congress, the states, and who gets sued."),
              ("deployment", "Deployment", "Where AI is actually being switched on: health systems, record vendors, the model companies, and AI-first care."),
              ("evidence", "Evidence", "What the studies and the professional societies say, and what nobody has shown yet."),
              ("money", "Money", "Funding rounds, valuations, acquisitions and the earnings calls that mention physician labor."),
              ("workforce", "Workforce", "Pay, staffing, productivity targets, scope-of-practice fights and how physicians say they feel about it."),
              ("incident", "Incidents", "Errors, recalls, lawsuits, breaches and enforcement.")]
cat_lookup = {}
for c in CATEGORIES:
    cat_lookup[c[0]] = c; cat_lookup[c[1].lower()] = c
topic_items = {c[0]: [] for c in CATEGORIES}
for slug, p in post_pages:
    for n, it in enumerate(p.get("items") or [], 1):
        if isinstance(it, str):
            continue
        c = cat_lookup.get((it.get("category") or "").strip().lower())
        if c:
            topic_items[c[0]].append((p.get("date") or "", slug, n, it))
topic_links = []
for key, label, blurb in CATEGORIES:
    entries = sorted(topic_items[key], key=lambda x: x[0], reverse=True)
    if not entries:
        continue
    path = "/topics/%s/" % key
    topic_links.append((path, label, len(entries)))
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">%s</h1><span class="sub">%d items from the daily posts</span></div>' % (esc(label), len(entries)),
            '<p class="lead">%s Each item links to the day it ran and to its original source.</p>' % esc(blurb), '<ul class="items">']
    for date, slug, n, it in entries:
        title = ext_link(it.get("title") or "", it["url"]) if it.get("url") else esc(it.get("title") or "")
        body.append('<li class="item"><div class="cat">%s  <span class="when"><a href="%s#item-%d" style="color:inherit">%s</a></span></div><div class="item-title">%s</div>'
                    % (esc(it.get("category") or label), post_url(slug), n, esc(fmt(it.get("date") or date)), title))
        if it.get("body"):
            body.append('<div class="item-body">%s</div>' % rich(it["body"]))
        body.append('<div class="item-src"><a href="%s#item-%d">From the %s post</a>%s</div></li>' % (post_url(slug), n, esc(fmt(date)), (" · " + sources_line("", it.get("sources"), it.get("source"), it.get("url")).replace('<div class="">', "").replace("</div>", "")) if (it.get("sources") or it.get("url")) else ""))
    body.append("</ul>")
    page(path, "%s: AI in medicine, item by item" % label, "%s Every item, newest first, linked to its source." % blurb,
         '<section class="panel">' + "".join(body) + "</section>", active="/posts/",
         jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": label, "url": absurl(path), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
    urls.append((path, LAST_UPDATED, "daily", "0.6"))
if topic_links:
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Topics</h1><span class="sub">the daily items, sorted by kind</span></div>',
            '<p class="lead">Every item from the daily posts, grouped by what kind of development it is.</p>', '<ul class="archive">']
    for path, label, n in topic_links:
        body.append('<li><span class="when">%d items</span><a href="%s">%s</a></li>' % (n, path, esc(label)))
    body.append("</ul>")
    page("/topics/", "Topics", "The daily items from %s grouped by kind: regulation, deployment, evidence, money, workforce and incidents." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/posts/")
    urls.append(("/topics/", LAST_UPDATED, "daily", "0.5"))

# ------------------------------------------------------------------ watch list
order = {"rising": 0, "active": 1, "favorable": 2, "quiet": 3}
body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Watch list</h1><span class="sub">the signals that would change the picture</span></div>',
        '<p class="lead">These are the things checked first every morning. A status changes only when something real happens, and the note says what.</p>',
        '<div class="legend"><span class="status rising">heating up</span><span class="status active">in motion</span><span class="status quiet">quiet</span><span class="status favorable">in our favor</span></div>',
        '<ul class="watch">']
for t in sorted(watchlist, key=lambda x: order.get(x.get("status"), 0)):
    st = t.get("status") or "quiet"
    body.append('<li><span class="status %s">%s</span><div><div class="name">%s</div>' % (esc(st), esc(STATUS.get(st, st)), esc(t.get("name", ""))))
    if t.get("note"):
        body.append('<div class="note">%s</div>' % rich(t["note"]))
    if t.get("last"):
        body.append('<div class="last">Last change <time datetime="%s">%s</time></div>' % (esc(t["last"]), esc(fmt(t["last"]))))
    body.append(sources_line("src", t.get("sources")) + "</div></li>")
body.append("</ul>")
page("/watch/", "Watch list", "The signals that would change the picture for physicians: Medicare payment for AI, FDA frameworks, autonomous prescribing, staffing, malpractice. Updated as they move.", '<section class="panel">' + "".join(body) + "</section>", active="/watch/")
urls.append(("/watch/", LAST_UPDATED, "daily", "0.7"))

# ------------------------------------------------------------------ dates
today_key = datetime.date.today().isoformat()
body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Dates that matter</h1><span class="sub">deadlines, effective dates, rules, meetings</span></div>']
last_month = None
for c in sorted(dates, key=lambda x: x.get("date") or ""):
    mk = (c.get("date") or "")[:7]
    if mk != last_month:
        if last_month is not None:
            body.append("</ul>")
        last_month = mk
        body.append('<div class="cal-month">%s</div><ul class="cal">' % esc(month_label(mk)))
    past = ' class="past"' if (c.get("date") and c["date"] < today_key) else ""
    title = ext_link(c.get("title", ""), c["url"]) if c.get("url") else esc(c.get("title", ""))
    body.append('<li%s><span class="d"><time datetime="%s">%s</time></span><div><div class="t">%s</div>%s</div></li>' % (past, esc(c.get("date", "")), esc(fmt(c.get("date"))), title, ('<div class="n">%s</div>' % rich(c["note"])) if c.get("note") else ""))
if last_month is not None:
    body.append("</ul>")
if not dates:
    body.append('<p class="empty">Nothing on the calendar yet.</p>')
page("/dates/", "Dates that matter", "Comment deadlines, effective dates, hearings and rules on AI in medicine, month by month, each linked to the page that sets it.", '<section class="panel">' + "".join(body) + "</section>", active="/dates/")
urls.append(("/dates/", LAST_UPDATED, "daily", "0.6"))

# ------------------------------------------------------------------ where things stand (long read)
land = section_html("landscape")
land = fix_internal_links(land)
m = re.search(r'<div class="panel-head">(.*?)</div>', land, re.S)
land_title = "Where things stand"
if m:
    land = land[:m.start()] + '<div class="crumbs">Where things stand · the long read</div>' + land[m.end():]
m = re.search(r'<h3[^>]*>(.*?)</h3>', land, re.S)
if m:
    land_title = re.sub(r"<[^>]+>", "", H.unescape(m.group(1))).strip()
    land = land[:m.start()] + '<h1 class="doc-title">%s</h1>' % m.group(1) + land[m.end():]
m = re.search(r'<p class="lede">(.*?)</p>', land, re.S)
land_desc = describe([re.sub(r"<[^>]+>", "", H.unescape(m.group(1)))]) if m else "A map of where AI in medicine stands: what the models can do, what runs without a doctor, the rules, the money, and what physicians should do."
ld_land = article_ld("Article", absurl("/where-things-stand/"), land_title, land_desc, LAST_UPDATED)
page("/where-things-stand/", land_title, land_desc, '<section class="panel doc">' + land + subscribe_box() + "</section>", active="/where-things-stand/", kind="article", jsonld=ld_land)
urls.append(("/where-things-stand/", LAST_UPDATED, "monthly", "0.8"))

# ------------------------------------------------------------------ about
# ------------------------------------------------------------------ podcast
if POD:
    ld_pod = {"@context": "https://schema.org", "@type": "PodcastSeries", "name": POD["name"], "url": absurl("/podcast/"), "webFeed": POD["rss"],
              "description": POD_BLURB, "inLanguage": "en-US", "author": PERSON, "publisher": PUBLISHER,
              "sameAs": [u for u in (POD.get("apple"), POD.get("spotify"), POD.get("youtube")) if u]}
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Podcast</h1><span class="sub">every episode, playable here</span></div>',
            '<p class="lead">%s Play any episode below, or follow the show in Apple Podcasts, Spotify or any app that takes an RSS feed.</p>' % esc(POD_BLURB),
            pod_embed("playlist", int(POD.get("playlist_height") or 390), "Every episode of the %s podcast" % POD["name"]),
            '<h2 class="pod-follow">Follow the show</h2>', pod_apps(),
            '<p class="pod-feed">In any other podcast app, add the feed: <code>%s</code></p>' % esc(POD["rss"]), POD_SCRIPT]
    page("/podcast/", "Podcast", "Every episode of the %s podcast, each morning's post as a short audio briefing, playable here or in Apple Podcasts and Spotify." % POD["name"],
         '<section class="panel">' + "".join(body) + "</section>", active="/podcast/", jsonld=ld_pod)
    urls.append(("/podcast/", LAST_UPDATED, "daily", "0.8"))

ld_about = {"@context": "https://schema.org", "@type": "AboutPage", "name": "About " + NAME, "url": absurl("/about/"), "mainEntity": {**PERSON, **({"image": absurl(photo_path)} if photo_path else {})}}
page("/about/", "About", "%s was created by %s, a family doctor in the mountains of Colorado, to sort what matters in AI in medicine from the noise." % (NAME, AUTHOR),
     '<section class="panel"><div class="panel-head"><h1 style="font-size:1.6rem">About</h1></div>' + about_inner + "</section>", active="/about/", jsonld=ld_about)
urls.append(("/about/", LAST_UPDATED, "monthly", "0.5"))

# ------------------------------------------------------------------ feed, sitemap, robots, extras
def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"

feed_items = []
for slug, p in post_pages:
    feed_items.append((p.get("date") or "", 2, p.get("headline") or "Daily post", absurl(post_url(slug)), describe(p.get("intro") or [p.get("headline")], 300), post_body(p)))
for slug, w in letter_pages:
    feed_items.append((w.get("weekOf") or "", 3, w.get("headline") or "The Friday letter", absurl(letter_url(slug)), plain(w.get("dek") or ""), (('<p><img src="%s" alt="%s" width="1200" height="630"></p>' % (esc(LETTER_IMG[slug][0] if LETTER_IMG[slug][0].startswith("https://") else absurl(LETTER_IMG[slug][0])), esc(LETTER_IMG[slug][1]))) if slug in LETTER_IMG else "") + paras(w.get("body")) + ('<div class="section-label">SOURCE MATERIAL</div>' + render_items(w["top"]) if w.get("top") else "") + (paras(w["outlook"]) if w.get("outlook") else "")))
for slug, sp in special_pages:
    feed_items.append((sp.get("date") or "", 1, sp.get("title") or "Special topic", absurl(special_url(slug)), plain(sp.get("dek") or ""), "".join("<p>%s</p>" % rich((b.get("lead", "") + " " + b.get("text", "")).strip()) for b in sp.get("blocks") or [])))
feed_items.sort(key=lambda x: (x[0], x[1]), reverse=True)
rss = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">',
       "<channel>", "<title>%s</title>" % esc(NAME), "<link>%s</link>" % esc(SITE), "<description>%s</description>" % esc(config["description"]),
       "<language>en-us</language>", '<atom:link href="%s" rel="self" type="application/rss+xml"/>' % esc(absurl("/feed.xml")),
       "<lastBuildDate>%s</lastBuildDate>" % rfc822(LAST_UPDATED), "<image><url>%s</url><title>%s</title><link>%s</link></image>" % (esc(absurl("/logo.png")), esc(NAME), esc(SITE))]
for date, _, title, link, desc, content in feed_items[:40]:
    rss.append("<item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s</guid><pubDate>%s</pubDate><dc:creator>%s</dc:creator><description>%s</description><content:encoded>%s</content:encoded></item>"
               % (esc(title), esc(link), esc(link), rfc822(date), esc(AUTHOR), esc(desc), cdata(content)))
rss.append("</channel></rss>")
write("/feed.xml", "\n".join(rss) + "\n")

sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, lastmod, freq, prio in urls:
    sm.append("<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>" % (esc(absurl(path)), esc(lastmod[:10]), freq, prio))
sm.append("</urlset>")
write("/sitemap.xml", "\n".join(sm) + "\n")
recent = [(slug, p) for slug, p in post_pages if p.get("date") and (datetime.date.today() - datetime.date.fromisoformat(p["date"][:10])).days <= 2 and not p.get("baseline")]
ns = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
for slug, p in recent:
    ns.append("<url><loc>%s</loc><news:news><news:publication><news:name>%s</news:name><news:language>en</news:language></news:publication><news:publication_date>%s</news:publication_date><news:title>%s</news:title></news:news></url>"
              % (esc(absurl(post_url(slug))), esc(NAME), iso_dt(p["date"]), esc(p.get("headline") or "Daily post")))
ns.append("</urlset>")
write("/sitemap-news.xml", "\n".join(ns) + "\n")
write("/robots.txt", "User-agent: *\nAllow: /\nSitemap: %s\nSitemap: %s\n" % (absurl("/sitemap.xml"), absurl("/sitemap-news.xml")))
write("/llms.txt", "# %s\n\n> %s\n\nWritten by %s. Daily posts are third-person news wire copy about artificial intelligence in medicine, each item linked to its original source; the Friday letter and the special topics are signed essays.\n\n## Sections\n\n- [Daily posts](%s): one post every morning, newest first\n- [Friday letter](%s): the weekly essay with recommendations\n- [Special topics](%s): long pieces on one question\n- [Watch list](%s): the signals that would change the picture\n- [Dates](%s): deadlines, effective dates, hearings\n- [Where things stand](%s): the long read\n- [Topics](%s): the daily items grouped by kind\n- [About](%s)\n- [RSS feed](%s)\n"
      % (NAME, config["description"], AUTHOR, absurl("/posts/"), absurl("/letters/"), absurl("/specials/"), absurl("/watch/"), absurl("/dates/"), absurl("/where-things-stand/"), absurl("/topics/"), absurl("/about/"), absurl("/feed.xml"))
      + ("- [Podcast](%s): each morning's post as a short audio briefing; podcast feed %s\n" % (absurl("/podcast/"), POD["rss"]) if POD else ""))

write("/favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#2F63A8"/>'
      '<path d="M20 14v18a12 12 0 0 0 24 0V14" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/><circle cx="32" cy="50" r="5" fill="#fff"/></svg>')
for name in ("og-image.png", "logo.png"):  # made once, kept in the repository's tools folder
    for cand in (os.path.join(ROOT, "tools", name), os.path.join(os.path.dirname(os.path.abspath(__file__)), name), os.path.join(ROOT, name)):
        if os.path.exists(cand):
            shutil.copyfile(cand, os.path.join(OUT, name)); break
    else:
        print("warning: %s not found; social previews will have no image" % name, file=sys.stderr)

write("/_redirects", "/subscribe  %s  302\n/substack   %s  302\n/newsletter %s  302\n/landscape/  /where-things-stand/  301\n/today/  /  301\n" % (SUBSCRIBE, SUBSTACK, SUBSTACK) + ("/listen  /podcast/  301\n" if POD else ""))
write("/_headers", "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
      "/images/*\n  Cache-Control: public, max-age=604800\n/og-image.png\n  Cache-Control: public, max-age=86400\n/logo.png\n  Cache-Control: public, max-age=604800\n")
page("/404.html", "Page not found", "That page is not here.", '<section class="panel"><div class="panel-head"><h1 style="font-size:1.6rem">That page is not here</h1></div><p class="lead">Try the <a href="/">front page</a>, the <a href="/posts/">daily posts</a>, or the <a href="/letters/">Friday letter</a>.</p></section>')
with open(os.path.join(ROOT, "netlify.toml"), "w") as f:
    f.write('[build]\n  publish = "public"\n  command = ""\n')

n_files = sum(len(fs) for _, _, fs in os.walk(OUT))
print("ok: built %d pages (%d posts, %d letters, %d specials), %d files in %s; updated %s; analytics %s" % (len(urls), len(post_pages), len(letter_pages), len(special_pages), n_files, OUT, LAST_UPDATED, (config.get("analytics") or {}).get("provider") or "none"))
