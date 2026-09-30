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
Version 2.4.1 (Sept 26, 2026): the footer and llms.txt credit the site as "Created by" the author (was "Written by").
Version 2.4.2 (Sept 26, 2026): the podcast blurb reads "Each morning's post as a short audio briefing, published every day."
Version 2.5 (Sept 26, 2026): the blurb, the /podcast/ description and llms.txt drop "short" ("Each morning's post as an audio
briefing, published every day."). Every daily post page (not the pinned launch post) ends with that day's episode player: the
page asks /api/episode/<date> when it loads and shows the player only once the episode is in the show's feed, because
episodes publish around 7:30 to 8:00 AM Mountain, after the 7:15 build. /api/episode/<date> is a Netlify function the script
writes to <repo root>/netlify/functions/episode.mjs (netlify.toml points Netlify at that folder); it reads the feed, finds the
item titled "Daily Update for <Month> <D>, <YYYY>" (config "episode_title") and answers with the Transistor id, cached on
Netlify's CDN for an hour when found and two minutes when not.
Version 2.6 (Sept 26, 2026): each Friday letter page carries the author's byline ("By Ryan Gillum, MD", from config "author")
under its standfirst, and a player for the letter's audio (read by the ElevenLabs voice Daniel, published to the same
Transistor show as "Friday Letter: <headline>") just under its illustration. The player stays hidden until
/api/letter/<weekOf> finds the episode: the same Netlify function now also answers that route, matching an episode whose
title starts with config podcast.letter_title_prefix ("Friday Letter") and whose show notes link to /letters/<weekOf>/.
Every letter is also written as plain text to /letters/<weekOf>/letter.json, and the newest to /letters/latest.json, which
is what the podcast pipeline reads to make the audio.
Version 2.7 (Sept 27, 2026): the daily post's episode player ("Listen to this post") sits just under the post's
illustration, above THE SHORT READ, on the post page and on the home page's today's post (under the headline when a post
has no picture), instead of at the foot of the page. The home page's separate "The daily podcast" section, which played
the latest episode after today's post, is gone: the post's own episode now plays under its picture. /podcast/ keeps the
full playlist and the follow links.
Version 2.8 (Sept 27, 2026): the Friday letter is unsigned, like a leader in The Economist. Letter pages no longer show a
byline; their meta author, their structured-data author (the publication, as an Organization) and their feed items'
dc:creator name the publication rather than the author, and letter.json and latest.json no longer carry a "byline" field.
Daily posts, special topics, the footer's "Created by" credit and the About page are unchanged.
Version 2.9 (Sept 27, 2026): the Friday letter archive (/letters/) shows each letter's illustration beside its entry
(above it on phones), linked to the letter, so the list reads as a set of covers; a letter without a picture keeps the
plain text entry. The pictures are the same files the letter pages use.
Version 2.10 (Sept 27, 2026): at the author's request the footer no longer says "Physician in the Loop. Created by
<author>. Daily on this site, weekly on Substack."; it keeps the tab links, "Not medical, legal, or financial advice.",
the Topics and RSS links and the copyright line. The default description follows the new masthead dek ("How artificial
intelligence changes medicine for patients and the people who practice on the front lines."); the live value comes from
site.config.json. llms.txt now describes the Friday letter as an unsigned editorial (it said the letter was a signed essay).
Version 2.11 (Sept 27, 2026): special topics can be written like the Friday letter. A special may carry "image" ({src,
alt}, the same form as a letter's), "top" (SOURCE MATERIAL items, the same form as a letter's) and "unsigned": true.
The picture is archived under assets/images/specials/, served from /images/specials/<slug>.<ext>, shown under the
standfirst on the special's page and used as its social image; the /specials/ list shows each special's picture beside
its entry, like /letters/. An unsigned special's meta author, structured-data author and feed dc:creator name the
publication, as for letters. The /specials/ page and llms.txt no longer promise "a step-by-step path" or "signed essays".
A special can be read aloud like a letter: every special is also written as plain text to /specials/<slug>/special.json
(for the podcast pipeline), and its page carries a "Listen to this special topic" player under the picture, hidden until
/api/special/<slug> finds the episode: the same Netlify function now also answers that route, matching an episode whose
title starts with config podcast.special_title_prefix ("Special Topic") and whose show notes link to /specials/<slug>/.
Version 2.12 (Sept 29, 2026): the standing references. The page's JSON may carry "laws" (the AI health law map: one entry per
state law, rule or bill: {id, state, category, also, kind, name, status, signed, effective, applies_to, summary, physician_read,
sources, checked, notes, added?, changed?, correction?}), "rhtp" (the Rural Health Transformation Program tracker, one row per
state), "explainers" ({slug, title, published, reviewed, short, blocks[h|p|list], changes, watch_for}) and "patients" (the
weekly letter for patients: {weekOf, date, headline, dek, intro, blocks[h|p|ask], question, closing}). Each becomes a section
whose tab appears in the navigation only when its list has entries: /law-map/ (a tile map of the 50 states shaded by the
laws and rules enacted or in force, with a category filter; what takes effect in the next 90 days; what was added or changed
in the last 30; how the map works; the data at /law-map/laws.json), /law-map/<state>/ (the state's entries by category),
/rhtp/ (open and upcoming funding rounds, a table and a card per state), /explainers/ and /explainers/<slug>/, and
/patients/ and /patients/<weekOf>/ with letter.json (plain text for reading aloud, the parenthetical source links left out)
and /patients/latest.json. The home page adds the newest letter for patients and links to the guides and trackers. An entry
marked "hidden": true is left out; a malformed entry is left out with a warning, and a section whose data breaks is skipped
with a warning, so a bad entry never stops the publish. "deployments" and "explainer_flags" are records for the daily task
and are not shown. feed.xml is unchanged.
Version 2.13 (Sept 29, 2026): the federal law page and reviewed states. The law map keeps entries with "state": "US". They use
the five state categories plus "devices", "payment" and "general" (FED_CATS, in the federal page's order: devices, clinical,
payer, payment, privacy, mental-health, disclosure, general) and the kinds "law", "rule", "guidance", "order" and "policy", with
their own status labels (Proposed, Draft, Final, Issued, In effect, In force, Revoked, Withdrawn) and date lines; state entries
render exactly as before. Federal entries get /law-map/federal/ (a count by status, the dates ahead, one section per federal
category with its cards and cross-references, and a last section for items withdrawn, revoked or failed), built when there is
at least one. The page's JSON may also carry "law_reviews", one record per reviewed jurisdiction (the 50 states and "US"):
{state, reviewed, note?, empty?: {category: text}}. A reviewed state with no entries gets its own page, saying nothing in the
map's scope was found in that review, and a linked, unshaded tile. On a state page (and the federal page) a category with no
entries of its own shows the review's "empty" text for it; with no such text, a state's empty category names the review's date.
A review's "note" follows the page's standfirst, and every state page ends with a line pointing to the federal page. /law-map/
now says it covers state and federal law and, once all 50 states are reviewed or on the map, that every state has been reviewed;
a state not yet reviewed keeps its gray tile, and the legend's "Not yet reviewed" key shows only while one remains. The page adds
a callout to the federal page and a line naming the states reviewed with none found, lists federal entries among the dates ahead
and the recent changes (when more than 8 entries were added on one day, they show as one line), and its "How the map works" box
describes the federal section. laws.json adds the federal entries, "federal_categories" and "reviews" (state and date), and
llms.txt lists the federal page. A malformed review is left out with a warning like a malformed entry, and the federal page, like
each section, is skipped with a warning if it breaks; nothing then links to it.
Version 2.13.1 (Sept 29, 2026): on law map pages, an entry's source list is separated by semicolons when any of its labels
contains a comma (for example "NAIC adoption map, Aug. 31, 2026"), so each source reads as one item; other pages are unchanged.
Version 2.14 (Sept 29, 2026): Cloudflare Pages. The script also writes <repo root>/functions/api/episode/[date].js,
functions/api/letter/[week].js and functions/api/special/[slug].js: Cloudflare Pages Functions that answer /api/episode/<date>,
/api/letter/<weekOf> and /api/special/<slug> with the same lookup as the Netlify function (the podcast feed is fetched through
Cloudflare's cache for two minutes, so a new episode shows within a few minutes). With them the repository can be served by
Cloudflare Pages (no build command, build output directory public), where public/_redirects, public/_headers and public/404.html
work as they do on Netlify. The Netlify function and netlify.toml are still written, so either host can publish the same commit.
The functions folder and the Netlify files are the only things outside public/ the script writes besides assets/images/.
Version 2.14.1 (Sept 29, 2026): the Rural Health Transformation Program tracker is retired. /rhtp/, its navigation tab, its
link on the home page and its llms.txt line are no longer built, and "rhtp" rows in the page JSON are ignored (with a note).
Version 2.14.2 (Sept 29, 2026): retired pages. Cloudflare Pages can keep serving a deleted page from a data center's cache for
up to a week after a deploy, so every path in RETIRED_PATHS (/rhtp/ and /specials/rural-health-transformation-program/) gets a
Pages Function (functions/<path>/index.js and [[path]].js) that answers with the site's not-found page and status 410 (Gone).
Version 2.15 (Sept 30, 2026): the publication speaks for itself. Every piece is credited to the publication: the meta author,
the structured-data author (an Organization) and the feed's dc:creator name Physician in the Loop, the home page no longer
carries a Person, llms.txt says the site is published by the copyright holder (Nomad Medical Group, LLC), and only the About page
names the founder (config "author", with "founder_title"), in its structured data as the founder of the copyright holder. The
navigation puts For patients last before About. A contact page: /contact/ has a form (name, email, topic, message, a hidden
honeypot field and a Cloudflare Turnstile check, site key from config contact.turnstile_sitekey) that posts to /api/contact, and
/contact/thanks/ thanks the sender. /api/contact is not a Pages Function: it is the Worker contact.worker, which checks the
Turnstile token and emails the message through an Email Routing send_email binding to the verified address contact.to. The script
writes that Worker's source and Wrangler configuration to <repo root>/contact-worker/ (src/index.js and wrangler.jsonc), which
Cloudflare Workers Builds deploys when that folder changes; the Turnstile secret key is a Worker secret (TURNSTILE_SECRET) set in the
dashboard and never kept in the repository. The form is linked (footer, About page, sitemap, llms.txt) and indexable only when
config contact.live is true; until then /contact/ is built but unlinked and marked noindex, so it can be tested before launch.
The podcast lookup now accepts every title in podcast.episode_titles ("Daily Briefing for <date>", the new name, and "Daily
Update for <date>", the old one), so the post pages find episodes under either name.
Version 2.15.1 (Sept 30, 2026): the contact Worker turns away any request body over 64 KB before reading it.
Version 2.16 (Sept 30, 2026): sharing and pictures. Every daily post, Friday letter, special topic and explainer page, the long
read (/where-things-stand/) and today's post on the home page carry a "Share story" link just under the standfirst (under the
headline where a piece has none) and above the picture. It opens the reader's share sheet where the browser has one
(navigator.share), otherwise copies the page's address and says "Link copied", and without JavaScript opens an email with the
title and address. /posts/ lists the daily posts the way /letters/ and /specials/ list theirs, each beside its picture.
Explainers may carry "image" ({src, alt}, the same form as a letter's): archived under assets/images/explainers/, served from
/images/explainers/<slug>.<ext>, shown under the share link on the explainer's page, used as its social image, and shown beside
the entry on /explainers/.
Version 2.16.1 (Sept 30, 2026): the letters for patients (/patients/<weekOf>/) carry the Share story link too, just under the
standfirst (they have no picture).
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
    "description": "How artificial intelligence changes medicine for patients and the people who practice on the front lines. Daily posts, a Friday letter and a podcast.",
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
        "episode_title": "Daily Briefing for {date}",
        "episode_titles": ["Daily Briefing for {date}", "Daily Update for {date}"],
        "letter_title_prefix": "Friday Letter",
        "special_title_prefix": "Special Topic",
    },
    "founder_title": "Founder and CEO",
    "contact": {
        "live": False,
        "to": "ryangillum@nomadmedical.org",
        "from": "contact-form@physicianintheloop.org",
        "turnstile_sitekey": "0x4AAAAAAFKXs504E3xIEBVc",
        "worker": "physicianintheloop-contact",
        "zone": "physicianintheloop.org",
        "path": "/api/contact",
        "compatibility_date": "2026-09-30",
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
if POD:
    # 2.15: every title a daily episode may carry; the configured episode_title first, then the rest in order
    _titles = [POD.get("episode_title")] + list(POD.get("episode_titles") or [])
    POD["episode_titles"] = [t for i, t in enumerate(_titles) if isinstance(t, str) and "{date}" in t and t not in _titles[:i]] or ["Daily Briefing for {date}", "Daily Update for {date}"]
CONTACT = None
if config.get("contact") is not False:
    CONTACT = dict(DEFAULT_CONFIG["contact"])
    if isinstance(config.get("contact"), dict):
        CONTACT.update({k: v for k, v in config["contact"].items() if v is not None and v != ""})
    if not (CONTACT.get("to") and CONTACT.get("from") and CONTACT.get("turnstile_sitekey") and CONTACT.get("worker") and CONTACT.get("zone")):
        CONTACT = None
CONTACT_LIVE = bool(CONTACT and CONTACT.get("live") is True)
PUBLISHED_BY = config.get("copyright_holder") or NAME

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

# ------------------------------------------------------------------ standing references (2.12): law map, program tracker, explainers, patient letters
STATES = [("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"), ("CA", "California"), ("CO", "Colorado"),
          ("CT", "Connecticut"), ("DE", "Delaware"), ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
          ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"), ("KY", "Kentucky"), ("LA", "Louisiana"),
          ("ME", "Maine"), ("MD", "Maryland"), ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
          ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"),
          ("NM", "New Mexico"), ("NY", "New York"), ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
          ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"), ("SD", "South Dakota"),
          ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"),
          ("WV", "West Virginia"), ("WI", "Wisconsin"), ("WY", "Wyoming")]
STATE_NAME = dict(STATES)
LAW_CATS = [("payer", "Payer and utilization review AI", "Insurers', benefit managers' and utilization reviewers' use of AI, including prior authorization and claim denials."),
            ("disclosure", "Patient disclosure of AI use", "Telling patients that AI is used in their care or in messages to them."),
            ("clinical", "Clinical decision and chatbot limits", "Limits on AI in clinical decisions and on health chatbots, including AI presenting itself as a licensed professional."),
            ("mental-health", "Mental health AI", "AI in therapy and mental health care."),
            ("privacy", "Data and privacy", "Health and consumer data, biometrics, and data used to train AI.")]
LAW_CAT_LABEL = {k: l for k, l, _ in LAW_CATS}
# 2.13: federal entries ("state": "US") use the five state categories and three of their own, in this order on /law-map/federal/
_STATE_CAT = {c[0]: c for c in LAW_CATS}
FED_CATS = [("devices", "Devices and FDA oversight", "FDA's oversight of AI-enabled medical devices and software, including clinical decision support and change control plans."),
            _STATE_CAT["clinical"], _STATE_CAT["payer"],
            ("payment", "Payment for AI", "How Medicare pays for AI-enabled services, software and devices."),
            _STATE_CAT["privacy"], _STATE_CAT["mental-health"], _STATE_CAT["disclosure"],
            ("general", "Government-wide AI policy", "Executive orders, OMB memoranda and federal strategies that reach AI in health care, including preemption of state AI laws.")]
FED_CAT_LABEL = {k: l for k, l, _ in FED_CATS}


def _iso(s):
    """True for a real YYYY-MM-DD date."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(s or "")):
        return False
    try:
        datetime.date.fromisoformat(str(s))
        return True
    except ValueError:
        return False


def _keep(label, rows, ok, key):
    """The usable entries of one list from the page: dicts that pass ok(), hidden ones left out, one per key.
    A malformed entry is left out with a warning; it never stops the publish."""
    kept, seen, bad = [], set(), 0
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, dict) and r.get("hidden"):
            continue
        try:
            good = isinstance(r, dict) and bool(ok(r))
        except Exception:
            good = False
        if not good:
            bad += 1
            continue
        k = key(r)
        if k in seen:
            continue
        seen.add(k)
        kept.append(r)
    if bad:
        print("warning: left out %d %s with missing or malformed fields" % (bad, label), file=sys.stderr)
    return kept


def _law_ok(e):
    """A usable law map entry: a state entry in one of the five categories, or a federal one ("US") in one of the eight, with a
    name or id. The fields the pages sort on or read as text must be text (or missing)."""
    if not all(e.get(f) is None or isinstance(e.get(f), str) for f in ("id", "name", "status", "kind", "effective")):
        return False
    if e.get("state") in STATE_NAME:
        in_scope = e.get("category") in LAW_CAT_LABEL
    else:
        in_scope = e.get("state") == "US" and e.get("category") in FED_CAT_LABEL
    return in_scope and (e.get("name") or e.get("id"))


def _review_ok(r):
    """A usable law_reviews record: {state (one of the 50, or "US"), reviewed (YYYY-MM-DD), note?, empty?: {category: text}}."""
    em = r.get("empty")
    return ((r.get("state") in STATE_NAME or r.get("state") == "US") and _iso(r.get("reviewed"))
            and (r.get("note") is None or isinstance(r.get("note"), str))
            and (em is None or (isinstance(em, dict) and all(v is None or isinstance(v, str) for v in em.values()))))


LAWS = _keep("law map entries", data.get("laws"), _law_ok, lambda e: e.get("id") or e.get("name"))   # state and federal entries
STATE_LAWS = [e for e in LAWS if e["state"] != "US"]
FED_LAWS = [e for e in LAWS if e["state"] == "US"]
LAW_REVIEWS = {r["state"]: r for r in _keep("law map reviews", data.get("law_reviews"), _review_ok, lambda r: r.get("state"))}
RHTP = []  # the Rural Health Transformation Program tracker was retired on Sept 29, 2026; any "rhtp" rows in the page JSON are ignored
if data.get("rhtp"):
    print("note: the page JSON has %d program tracker rows; the tracker is retired and they are not published" % len(data.get("rhtp") or []), file=sys.stderr)
EXPLAINERS = _keep("explainers", data.get("explainers"),
                   lambda x: x.get("title") and re.match(r"^[a-z0-9][a-z0-9-]{0,79}$", x.get("slug") or ""), lambda x: x.get("slug"))
PATIENTS = sorted(_keep("patient letters", data.get("patients"), lambda x: _iso(x.get("weekOf")) and x.get("headline"), lambda x: x.get("weekOf")),
                  key=lambda x: x["weekOf"], reverse=True)

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

def sources_line(cls, srcs, fallback_label=None, fallback_url=None, sep=", "):
    srcs = srcs if srcs else ([{"label": fallback_label or fallback_url, "url": fallback_url}] if (fallback_label or fallback_url) else [])
    if not srcs:
        return ""
    bits = []
    for s in srcs:
        if s.get("url"):
            bits.append(ext_link(s.get("label") or s["url"], s["url"]))
        else:
            bits.append(esc(s.get("label") or ""))
    return '<div class="%s">%s%s</div>' % (cls, "Sources: " if len(srcs) > 1 else "Source: ", sep.join(bits))

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

def post_body(p, anchors=False, fig="", under_fig=""):
    out = [x for x in (fig, under_fig) if x]
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
FED_URL = "/law-map/federal/"
def law_state_url(code): return FED_URL if code == "US" else "/law-map/%s/" % slugify(STATE_NAME.get(code, code))
def explainer_url(slug): return "/explainers/%s/" % slug
def patient_url(week): return "/patients/%s/" % week

NAV = ([("/", "Today")] + ([("/podcast/", "Podcast")] if POD else []) + [("/posts/", "Daily posts"), ("/letters/", "Friday letter")]
       + [("/specials/", "Special topics")]
       + ([("/law-map/", "Law map")] if LAWS else []) + ([("/rhtp/", "RHTP tracker")] if RHTP else []) + ([("/explainers/", "Explainers")] if EXPLAINERS else [])
       + [("/watch/", "Watch list"), ("/dates/", "Dates"), ("/where-things-stand/", "Where things stand")]
       + ([("/patients/", "For patients")] if PATIENTS else []) + [("/about/", "About")])
HASH_MAP = {"today": "/", "podcast": "/podcast/", "posts": "/posts/", "letters": "/letters/", "specials": "/specials/", "watch": "/watch/", "dates": "/dates/", "landscape": "/where-things-stand/", "about": "/about/"}
HASH_MAP.update({k: v for k, v, have in (("patients", "/patients/", PATIENTS), ("lawmap", "/law-map/", LAWS), ("rhtp", "/rhtp/", RHTP), ("explainers", "/explainers/", EXPLAINERS)) if have})
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
  .letter-audio { margin: 0 0 24px; }
  .letter-audio-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 4px 16px; margin: 0 0 10px; }
  .letter-audio-head h2 { font-size: 1.05rem; margin: 0; }
  .letter-audio-head .sub { font-size: 0.85rem; color: var(--muted); }
  .letter-audio + .body-copy { margin-top: 0; }
  .post-episode { margin: 16px 0 0; }
  .post-episode-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 4px 16px; margin: 0 0 10px; }
  .post-episode-head h2 { font-size: 1.05rem; margin: 0; }
  .post-episode-head .sub { font-size: 0.85rem; }
  .post-episode + .section-label { margin-top: 24px; }
  .letter-list { list-style: none; margin: 8px 0 0; padding: 0; }
  .letter-list li { display: grid; grid-template-columns: minmax(0, 250px) minmax(0, 1fr); gap: 12px 22px; align-items: start; padding-block: 20px; border-top: 1px solid var(--rule); }
  .letter-list li:last-child { border-bottom: 1px solid var(--rule); }
  .letter-list li.no-thumb { grid-template-columns: minmax(0, 1fr); }
  .letter-list .thumb { display: block; border-radius: 10px; }
  .letter-list .thumb img { display: block; width: 100%; height: auto; aspect-ratio: 1200 / 630; object-fit: cover; border-radius: 10px; border: 1px solid var(--rule); box-shadow: var(--shadow); background: var(--bg-2); transition: transform .15s ease; }
  .letter-list .thumb:hover img { transform: translateY(-2px); }
  .letter-list .txt { min-width: 0; }
  .letter-list .when { display: block; font-family: var(--mono); font-size: 0.72rem; color: var(--muted); letter-spacing: 0.04em; }
  .letter-list .t { display: block; margin-top: 4px; font-family: var(--display); font-weight: 600; font-size: 1.25rem; line-height: 1.25; color: var(--ink); text-decoration: none; }
  .letter-list .t:hover { color: var(--accent-2); }
  .letter-list .d { margin: 8px 0 0; font-size: 0.97rem; line-height: 1.5; color: var(--ink-2); }
  @media (max-width: 600px) { .letter-list li { grid-template-columns: minmax(0, 1fr); gap: 12px; } }
  @media (prefers-reduced-motion: reduce) { .letter-list .thumb img { transition: none; } .letter-list .thumb:hover img { transform: none; } }
  .ref-row { display: flex; flex-wrap: wrap; gap: 10px; }
  .chip { appearance: none; display: inline-block; font-family: var(--body); font-size: 0.85rem; font-weight: 600; color: var(--accent-2); background: var(--surface); border: 1px solid var(--accent-line); border-radius: 999px; padding: 6px 12px; cursor: pointer; line-height: 1.2; text-decoration: none; }
  .chip:hover { background: var(--accent-soft); color: var(--accent-2); }
  .chip[aria-pressed="true"] { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
  .lawmap-filter { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 16px; }
  .tilemap { display: grid; grid-template-columns: repeat(11, minmax(0, 1fr)); gap: 4px; max-width: 640px; margin: 6px 0 12px; }
  .tile { aspect-ratio: 1 / 1; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-family: var(--mono); font-size: clamp(0.54rem, 1.9vw, 0.8rem); font-weight: 500; text-decoration: none; border: 1px solid transparent; line-height: 1; min-width: 0; }
  .tile.nr, .tile-key.nr { background: var(--surface-2); color: var(--muted); border-color: var(--rule); }
  .tile.nr { opacity: 0.8; }
  .tile.lv-0, .tile-key.lv-0 { background: var(--surface); color: var(--ink-2); border-color: var(--accent-line); }
  .tile.lv-1, .tile-key.lv-1 { background: var(--accent-soft); background: color-mix(in srgb, var(--accent) 28%, var(--surface)); color: var(--ink); }
  .tile.lv-2, .tile-key.lv-2 { background: var(--accent-line); background: color-mix(in srgb, var(--accent) 58%, var(--surface)); color: var(--ink); }
  .tile.lv-3, .tile-key.lv-3 { background: var(--accent-2); color: var(--accent-ink); }
  a.tile:hover { outline: 2px solid var(--accent); outline-offset: 1px; }
  .tile-legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 0.85rem; color: var(--muted); align-items: center; }
  .tile-legend span { display: inline-flex; align-items: center; gap: 6px; }
  .tile-key { display: inline-block; width: 14px; height: 14px; border-radius: 3px; border: 1px solid transparent; }
  .tile-cap { font-size: 0.85rem; color: var(--muted); margin: 6px 0 0; }
  .tile-states { font-size: 0.95rem; margin: 12px 0 0; color: var(--ink-2); }
  .lm-h { font-size: 1.3rem; margin: 30px 0 8px; }
  .lm-note { color: var(--ink-2); font-size: 0.97rem; margin: 0 0 10px; }
  .archive .rt a { font-family: var(--display); font-weight: 600; font-size: 1.08rem; line-height: 1.3; }
  .archive li > div { min-width: 0; }
  .method { margin-top: 30px; padding: 18px 20px; background: var(--surface); border: 1px solid var(--rule); border-radius: 12px; font-size: 0.95rem; color: var(--ink-2); }
  .method h2 { font-size: 1.1rem; margin-bottom: 8px; }
  .method p { margin: 0 0 10px; }
  .method p:last-child { margin-bottom: 0; }
  .law { background: var(--surface); border: 1px solid var(--rule); border-radius: 14px; padding: 18px 20px 16px; box-shadow: var(--shadow); margin: 14px 0; }
  @media (max-width: 480px) { .law { padding: 16px 16px 14px; } }
  .law-top { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .lstat { display: inline-block; font-family: var(--mono); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.1em; padding: 4px 9px; border-radius: 999px; font-weight: 500; line-height: 1.3; vertical-align: 1px; }
  .lstat.st-effective, .lstat.st-open { color: var(--good); background: rgba(44, 122, 85, 0.11); }
  .lstat.st-enacted, .lstat.st-upcoming { color: var(--warn); background: rgba(166, 102, 15, 0.11); }
  .lstat.st-passed, .lstat.st-introduced, .lstat.st-awarded { color: var(--accent-2); background: var(--accent-soft); }
  .lstat.st-failed, .lstat.st-closed { color: var(--muted); background: var(--surface-2); }
  .lstat.st-blocked { color: var(--bad); background: rgba(178, 59, 59, 0.10); }
  .law-kind { font-family: var(--mono); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
  .law-name { font-size: 1.15rem; margin-top: 8px; line-height: 1.3; }
  .law-dates { font-size: 0.92rem; color: var(--accent-2); margin-top: 4px; font-weight: 600; }
  .law-sum { margin: 10px 0 0; color: var(--ink-2); }
  .law-read { margin: 12px 0 0; padding: 10px 14px; background: var(--accent-soft); border-left: 3px solid var(--accent); border-radius: 0 10px 10px 0; color: var(--ink); }
  .law-meta { margin: 10px 0 0; font-size: 0.93rem; color: var(--ink-2); }
  .law-src { font-size: 0.86rem; color: var(--muted); margin-top: 8px; }
  .law-src a { color: var(--muted); }
  .law-notes { font-size: 0.88rem; color: var(--muted); margin: 8px 0 0; }
  .law-checked { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); margin-top: 8px; }
  .law-cat { margin-top: 30px; }
  .law-cat > h2 { font-size: 1.35rem; }
  .law-cat-note { color: var(--muted); font-size: 0.93rem; margin: 4px 0 0; }
  .law-also { font-size: 0.93rem; color: var(--ink-2); margin: 10px 0 0; }
  .law-toc { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 0; }
  .law-foot { margin-top: 26px; font-size: 0.9rem; color: var(--muted); }
  .lawstate .standfirst { margin-bottom: 4px; }
  .rhtp-state { background: var(--surface); border: 1px solid var(--rule); border-radius: 16px; padding: 20px 22px; box-shadow: var(--shadow); margin-top: 22px; }
  @media (max-width: 480px) { .rhtp-state { padding: 18px 16px; } }
  .rhtp-state h2 { font-size: 1.4rem; }
  .facts { display: grid; grid-template-columns: 180px minmax(0, 1fr); gap: 10px 18px; margin: 12px 0 0; }
  .facts dt { font-family: var(--mono); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent-2); padding-top: 5px; }
  .facts dd { margin: 0; color: var(--ink-2); min-width: 0; overflow-wrap: anywhere; }
  .facts ul { margin: 0; padding-left: 1.1em; }
  .facts li + li { margin-top: 8px; }
  @media (max-width: 560px) { .facts { grid-template-columns: minmax(0, 1fr); gap: 2px; } .facts dd { margin-bottom: 12px; } }
  .short-answer { margin: 18px 0 8px; padding: 16px 20px; background: var(--accent-soft); border-left: 3px solid var(--accent); border-radius: 0 12px 12px 0; }
  .short-answer h2, .changes h2, .one-question h2 { font-family: var(--mono); font-weight: 500; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--accent-2); margin: 0 0 8px; }
  .short-answer p { margin: 0; font-size: 1.06rem; color: var(--ink); }
  .explainer-body h2, .patient-body h2 { font-family: var(--display); font-size: 1.32rem; font-weight: 600; margin: 30px 0 10px; }
  .explainer-body ol, .explainer-body ul { padding-left: 1.3em; margin: 0 0 14px; }
  .explainer-body li { margin: 0 0 8px; font-size: 1.02rem; line-height: 1.6; }
  .changes { margin-top: 26px; padding: 16px 20px; background: var(--surface-2); border-radius: 12px; }
  .changes p { margin: 0; color: var(--ink-2); }
  .explainer-foot { font-size: 0.88rem; color: var(--muted); margin: 18px 0 0; }
  .patient-note { font-size: 0.88rem; color: var(--muted); margin: 12px 0 0; padding: 10px 14px; border: 1px dashed var(--rule-2); border-radius: 10px; }
  .patient-intro { font-style: italic; color: var(--ink-2); }
  .special-body p.ask { background: var(--surface-2); border-radius: 10px; padding: 10px 14px; }
  .special-body p.ask strong { color: var(--accent-2); }
  .one-question { margin-top: 26px; padding: 18px 20px; background: var(--accent-soft); border-left: 3px solid var(--accent); border-radius: 0 12px 12px 0; }
  .one-question p { margin: 0; font-family: var(--display); font-size: 1.2rem; color: var(--ink); line-height: 1.45; }
  .patient-closing { margin-top: 18px; color: var(--ink-2); }
  .share-row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: 14px 0 0; }
  .btn.share-link { display: inline-flex; align-items: center; gap: 7px; }
  .btn.share-link svg { width: 16px; height: 16px; flex: 0 0 auto; }
  .share-note { font-size: 0.85rem; color: var(--muted); }
  .share-note:empty { display: none; }
  .doc .share-row { margin: 0 0 22px; }
  .explainer .letter-art + .short-answer { margin-top: 0; }
  .post-list .t { font-size: 1.12rem; line-height: 1.3; }
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
        '</div><p style="margin-top:10px">Not medical, legal, or financial advice. <a href="/topics/">Topics</a>. <a href="/feed.xml">RSS</a>.'
        + (' <a href="/contact/">Contact us</a>.' if CONTACT_LIVE else "") + '</p>'
        '<p class="copyright">&copy; %d %s. All rights reserved.</p></footer>' % (datetime.date.today().year, esc(config.get("copyright_holder") or AUTHOR)))

def page(path, title, desc, body, active=None, kind="website", jsonld=None, published=None, modified=None, head_extra="", image=None, image_alt=None, unsigned=True, noindex=False):
    # 2.15: every page is credited to the publication; "unsigned" is kept for callers but no page names a person as author
    url = absurl(path)
    og_img = (absurl(image) if image.startswith("/") else image) if image else absurl("/og-image.png")
    full_title = title if (title.startswith(NAME) or title.endswith(NAME)) else "%s | %s" % (title, NAME)
    head = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            '<title>%s</title>' % esc(full_title),
            '<meta name="description" content="%s">' % esc(desc),
            '<meta name="author" content="%s">' % esc(NAME),
            '<meta name="robots" content="%s">' % ("noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"),
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

PUBLISHER = {"@type": "Organization", "name": NAME, "url": SITE, "logo": {"@type": "ImageObject", "url": absurl("/logo.png"), "width": 512, "height": 512},
             **({"parentOrganization": {"@type": "Organization", "name": PUBLISHED_BY}} if PUBLISHED_BY != NAME else {})}
ORG_AUTHOR = {"@type": "Organization", "name": NAME, "url": SITE}
# 2.15: the founder appears only on the About page, as the founder of the copyright holder
FOUNDER = {"@type": "Person", "name": AUTHOR, "jobTitle": config.get("founder_title") or "Founder and CEO"}

def article_ld(kind, url, headline, desc, date, image=None, unsigned=True):
    return {"@context": "https://schema.org", "@type": kind, "headline": headline[:110], "description": desc,
            "datePublished": iso_dt(date), "dateModified": iso_dt(date if date != LAST_UPDATED else LAST_UPDATED),
            "author": ORG_AUTHOR, "publisher": PUBLISHER, "mainEntityOfPage": {"@type": "WebPage", "@id": url},
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

POD_BLURB = "Each morning's post as an audio briefing, published every day."
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

EPISODE_SCRIPT = ('<script>(function(){var s=document.getElementById("post-episode");if(!s||!window.fetch)return;'
                  'fetch("/api/episode/"+s.getAttribute("data-date")).then(function(r){return r.ok?r.json():null})'
                  '.then(function(e){if(!e||!e.found||!/^[a-z0-9]+$/i.test(e.id||""))return;var d=false;'
                  'try{d=window.matchMedia("(prefers-color-scheme: dark)").matches}catch(x){}'
                  's.querySelector("iframe").src="https://share.transistor.fm/e/"+e.id+(d?"/dark":"");s.hidden=false})'
                  '.catch(function(){})})();</script>')

def episode_block(date):
    """That day's episode player, just under the post's illustration. It stays hidden until /api/episode/<date> finds the episode."""
    if not (POD and re.match(r"^\d{4}-\d{2}-\d{2}$", date or "")):
        return ""
    return ('<section class="post-episode" id="post-episode" data-date="%s" hidden aria-label="Listen to this post">'
            '<div class="post-episode-head"><h2>Listen to this post</h2><a class="sub" href="/podcast/">all episodes</a></div>'
            '<div class="pod-player"><iframe title="Podcast episode for this post" height="180" scrolling="no"></iframe></div></section>' % esc(date)
            + EPISODE_SCRIPT)

LETTER_AUDIO_SCRIPT = ('<script>(function(){var s=document.getElementById("letter-audio");if(!s||!window.fetch)return;'
                       'fetch("/api/letter/"+s.getAttribute("data-week")).then(function(r){return r.ok?r.json():null})'
                       '.then(function(e){if(!e||!e.found||!/^[a-z0-9]+$/i.test(e.id||""))return;var d=false;'
                       'try{d=window.matchMedia("(prefers-color-scheme: dark)").matches}catch(x){}'
                       's.querySelector("iframe").src="https://share.transistor.fm/e/"+e.id+(d?"/dark":"");s.hidden=false})'
                       '.catch(function(){})})();</script>')

SPECIAL_AUDIO_SCRIPT = ('<script>(function(){var s=document.getElementById("special-audio");if(!s||!window.fetch)return;'
                        'fetch("/api/special/"+s.getAttribute("data-slug")).then(function(r){return r.ok?r.json():null})'
                        '.then(function(e){if(!e||!e.found||!/^[a-z0-9]+$/i.test(e.id||""))return;var d=false;'
                        'try{d=window.matchMedia("(prefers-color-scheme: dark)").matches}catch(x){}'
                        's.querySelector("iframe").src="https://share.transistor.fm/e/"+e.id+(d?"/dark":"");s.hidden=false})'
                        '.catch(function(){})})();</script>')

def special_audio_block(slug):
    """The special topic read aloud, just under its picture. Hidden until /api/special/<slug> finds the episode."""
    if not (POD and re.match(r"^[a-z0-9][a-z0-9-]{0,79}$", slug or "")):
        return ""
    return ('<section class="letter-audio" id="special-audio" data-slug="%s" hidden aria-label="Listen to this special topic">'
            '<div class="letter-audio-head"><h2>Listen to this special topic</h2><span class="sub">read by an AI voice</span></div>'
            '<div class="pod-player"><iframe title="This special topic, read aloud" height="180" scrolling="no" loading="lazy"></iframe></div></section>' % esc(slug)
            + SPECIAL_AUDIO_SCRIPT)

def letter_audio_block(week):
    """The letter read aloud, just under its illustration. Hidden until /api/letter/<weekOf> finds the episode."""
    if not (POD and re.match(r"^\d{4}-\d{2}-\d{2}$", week or "")):
        return ""
    return ('<section class="letter-audio" id="letter-audio" data-week="%s" hidden aria-label="Listen to this letter">'
            '<div class="letter-audio-head"><h2>Listen to this letter</h2><span class="sub">read by an AI voice</span></div>'
            '<div class="pod-player"><iframe title="This letter, read aloud" height="180" scrolling="no" loading="lazy"></iframe></div></section>' % esc(week)
            + LETTER_AUDIO_SCRIPT)

EPISODE_FN = r'''// Podcast episode lookup for physicianintheloop.org. Written by tools/build_public_site.py on every
// site build; edit the generator, not this file.
//
// GET /api/episode/YYYY-MM-DD finds the episode titled for that date (under any name in TITLES) in the show's feed and answers
// {"found": true, "id": "...", "embed": "https://share.transistor.fm/e/<id>", ...}, or {"found": false}
// before the episode exists. Daily post pages call it when they load and show the player only when found.
// Answers are cached on Netlify's CDN: a found episode for an hour, a missing one for two minutes, so a
// new episode appears on its post page within a few minutes of publishing.
//
// GET /api/letter/YYYY-MM-DD (the letter's weekOf) finds the Friday letter's audio: an episode whose title
// starts with LETTER_PREFIX and whose show notes link to /letters/<weekOf>/. Letter pages show their player
// only when it is found.
//
// GET /api/special/<slug> finds a special topic's audio the same way: an episode whose title starts with
// SPECIAL_PREFIX and whose show notes link to /specials/<slug>/.

const FEED = __FEED__;
const TITLES = __TITLES__;
const LETTER_PREFIX = __LETTER__;
const SPECIAL_PREFIX = __SPECIAL__;
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function titlesFor(date) {
  const [y, m, d] = date.split("-").map(Number);
  const when = MONTHS[m - 1] + " " + d + ", " + y;
  return TITLES.map((t) => t.replace("{date}", when));
}

function plain(s) {
  return s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function reply(body, status, browserCache, cdnCache) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": browserCache,
      "netlify-cdn-cache-control": cdnCache,
    },
  });
}

function episodeId(item) {
  const link =
    /<link>\s*https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item) ||
    /<enclosure[^>]+https:\/\/media\.transistor\.fm\/([a-z0-9]+)\//i.exec(item) ||
    /https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item);
  return link ? link[1] : null;
}

export default async (req, context) => {
  const params = (context && context.params) || {};
  const query = new URL(req.url).searchParams;
  const reqPath = new URL(req.url).pathname;
  if (params.slug || reqPath.startsWith("/api/special/")) {
    const slug = params.slug || reqPath.split("/")[3] || "";
    if (!/^[a-z0-9][a-z0-9-]{0,79}$/.test(slug)) {
      return reply({ found: false, error: "bad slug" }, 400, "public, max-age=86400", "public, s-maxage=86400");
    }
    let sxml;
    try {
      const res = await fetch(FEED, { headers: { "user-agent": "physicianintheloop.org episode lookup" } });
      if (!res.ok) throw new Error("feed answered " + res.status);
      sxml = await res.text();
    } catch (err) {
      return reply({ found: false, error: "feed unavailable" }, 502, "no-store", "no-store");
    }
    const sprefix = plain(SPECIAL_PREFIX);
    const specialPath = "/specials/" + slug + "/";
    for (const chunk of sxml.split(/<item[\s>]/i).slice(1)) {
      const item = chunk.split(/<\/item>/i)[0];
      const titles = [...item.matchAll(/<(?:itunes:)?title>([\s\S]*?)<\/(?:itunes:)?title>/gi)].map((x) => plain(x[1]));
      if (!titles.some((x) => x.startsWith(sprefix)) || !item.includes(specialPath)) continue;
      const id = episodeId(item);
      if (!id) continue;
      return reply(
        { found: true, slug, title: titles[0], id, share: "https://share.transistor.fm/s/" + id, embed: "https://share.transistor.fm/e/" + id },
        200,
        "public, max-age=600",
        "public, s-maxage=3600, stale-while-revalidate=86400"
      );
    }
    return reply({ found: false, slug }, 200, "public, max-age=60", "public, s-maxage=120");
  }
  const week = params.week || (new URL(req.url).pathname.startsWith("/api/letter/") ? new URL(req.url).pathname.split("/")[3] : "") || query.get("week") || "";
  const isLetter = Boolean(week);
  const date = isLetter ? week : params.date || query.get("date") || "";
  const parts = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!parts || +parts[2] < 1 || +parts[2] > 12 || +parts[3] < 1 || +parts[3] > 31) {
    return reply({ found: false, error: "bad date" }, 400, "public, max-age=86400", "public, s-maxage=86400");
  }
  let xml;
  try {
    const res = await fetch(FEED, { headers: { "user-agent": "physicianintheloop.org episode lookup" } });
    if (!res.ok) throw new Error("feed answered " + res.status);
    xml = await res.text();
  } catch (err) {
    return reply({ found: false, error: "feed unavailable" }, 502, "no-store", "no-store");
  }
  if (isLetter) {
    const prefix = plain(LETTER_PREFIX);
    const letterPath = "/letters/" + date + "/";
    for (const chunk of xml.split(/<item[\s>]/i).slice(1)) {
      const item = chunk.split(/<\/item>/i)[0];
      const titles = [...item.matchAll(/<(?:itunes:)?title>([\s\S]*?)<\/(?:itunes:)?title>/gi)].map((t) => plain(t[1]));
      if (!titles.some((t) => t.startsWith(prefix)) || !item.includes(letterPath)) continue;
      const id = episodeId(item);
      if (!id) continue;
      return reply(
        { found: true, week: date, title: titles[0], id, share: "https://share.transistor.fm/s/" + id, embed: "https://share.transistor.fm/e/" + id },
        200,
        "public, max-age=600",
        "public, s-maxage=3600, stale-while-revalidate=86400"
      );
    }
    return reply({ found: false, week: date }, 200, "public, max-age=60", "public, s-maxage=120");
  }
  const wanted = titlesFor(date);
  const wants = wanted.map(plain);
  for (const chunk of xml.split(/<item[\s>]/i).slice(1)) {
    const item = chunk.split(/<\/item>/i)[0];
    const titles = [...item.matchAll(/<(?:itunes:)?title>([\s\S]*?)<\/(?:itunes:)?title>/gi)].map((t) => plain(t[1]));
    const hit = wants.findIndex((w) => titles.includes(w));
    if (hit === -1) continue;
    const link =
      /<link>\s*https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item) ||
      /<enclosure[^>]+https:\/\/media\.transistor\.fm\/([a-z0-9]+)\//i.exec(item) ||
      /https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item);
    if (!link) continue;
    const id = link[1];
    return reply(
      { found: true, date, title: wanted[hit], id, share: "https://share.transistor.fm/s/" + id, embed: "https://share.transistor.fm/e/" + id },
      200,
      "public, max-age=600",
      "public, s-maxage=3600, stale-while-revalidate=86400"
    );
  }
  return reply({ found: false, date }, 200, "public, max-age=60", "public, s-maxage=120");
};

export const config = { path: ["/api/episode/:date", "/api/letter/:week", "/api/special/:slug"] };
'''

CF_ROUTES = (("episode", "[date].js"), ("letter", "[week].js"), ("special", "[slug].js"))
# Pages taken off the site on purpose. Cloudflare Pages can keep serving a deleted page from a data center's cache for up to a
# week after a deploy, so each retired path gets a Pages Function that answers with the site's not-found page and status 410.
RETIRED_PATHS = ("/rhtp", "/specials/rural-health-transformation-program")
RETIRED_FN = r"""// Retired page on physicianintheloop.org: __PATH__/. Written by tools/build_public_site.py on every site build;
// edit the generator, not this file.
//
// The page that lived here was taken off the site on purpose. This function answers every request for it with the
// site's "not found" page and status 410 (Gone), so the old page is never served again, even by a data center that
// still holds a cached copy.

const FALLBACK = '<!doctype html><meta charset="utf-8"><title>Page not found | Physician in the Loop</title>' +
  '<p>That page is not here. Try the <a href="/">front page</a>.</p>';

async function notFoundPage(context) {
  const origin = new URL(context.request.url).origin;
  for (const path of ["/404", "/404.html"]) {
    try {
      let res = await context.env.ASSETS.fetch(new Request(origin + path));
      if (res.status >= 300 && res.status < 400 && res.headers.get("location")) {
        res = await context.env.ASSETS.fetch(new Request(new URL(res.headers.get("location"), origin).toString()));
      }
      const type = res.headers.get("content-type") || "";
      if ((res.status === 200 || res.status === 404) && type.includes("text/html")) return await res.text();
    } catch (err) {}
  }
  return FALLBACK;
}

export async function onRequest(context) {
  return new Response(await notFoundPage(context), {
    status: 410,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" },
  });
}
"""


def cloudflare_function_source():
    """The Netlify function's lookup, adapted to a Cloudflare Pages Function (onRequest(context)); the same text serves all three routes."""
    src = (EPISODE_FN.replace("__FEED__", json.dumps(POD["rss"]))
           .replace("__TITLES__", json.dumps(POD["episode_titles"]))
           .replace("__LETTER__", json.dumps(POD.get("letter_title_prefix") or "Friday Letter"))
           .replace("__SPECIAL__", json.dumps(POD.get("special_title_prefix") or "Special Topic")))
    swaps = [
        ('"netlify-cdn-cache-control": cdnCache,', '"cdn-cache-control": cdnCache,'),
        ('export default async (req, context) => {\n  const params = (context && context.params) || {};',
         'async function handle(req, params) {\n  params = params || {};'),
        ('{ headers: { "user-agent": "physicianintheloop.org episode lookup" } }',
         '{ headers: { "user-agent": "physicianintheloop.org episode lookup" }, cf: { cacheTtl: 120, cacheEverything: true } }'),
        ('\nexport const config = { path: ["/api/episode/:date", "/api/letter/:week", "/api/special/:slug"] };\n', '\n'),
        ('// Answers are cached on Netlify\'s CDN: a found episode for an hour, a missing one for two minutes, so a\n// new episode appears on its post page within a few minutes of publishing.',
         '// This is the Cloudflare Pages version of netlify/functions/episode.mjs: the same lookup, with the feed fetched\n// through Cloudflare\'s cache for two minutes, so a new episode appears on its page within a few minutes.'),
    ]
    for old, new in swaps:
        if old not in src:
            raise ValueError("Cloudflare function template out of step with the Netlify one: %r" % old[:60])
        src = src.replace(old, new)
    return src + "\nexport async function onRequest(context) {\n  return handle(context.request, context.params);\n}\n"


def write_cloudflare_functions():
    """Write (or remove) the Cloudflare Pages Functions behind /api/episode, /api/letter and /api/special. True when written."""
    base = os.path.join(ROOT, "functions", "api")
    targets = [os.path.join(base, folder, name) for folder, name in CF_ROUTES]
    if not POD:
        for t in targets:
            if os.path.exists(t):
                os.remove(t)
        return False
    src = cloudflare_function_source()
    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "w", encoding="utf-8") as f:
            f.write(src)
    return True


def write_retired_functions():
    """Write a Pages Function for each retired path (index.js for the path itself, [[path]].js for anything under it)."""
    written = 0
    for path in RETIRED_PATHS:
        folder = os.path.join(ROOT, "functions", *path.strip("/").split("/"))
        os.makedirs(folder, exist_ok=True)
        for name in ("index.js", "[[path]].js"):
            with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
                f.write(RETIRED_FN.replace("__PATH__", path))
            written += 1
    return written


CONTACT_WORKER_JS = r"""// Contact form Worker for physicianintheloop.org (route __ROUTE__). Written by tools/build_public_site.py on every
// site build; edit the generator, not this file. Cloudflare Workers Builds deploys this folder when it changes.
//
// The form at /contact/ posts here. The Worker checks the Cloudflare Turnstile token (secret TURNSTILE_SECRET, set in
// the dashboard and never kept in the repository), emails the message through the Email Routing binding SEND_EMAIL to the
// verified destination address, and sends the visitor back to /contact/thanks/ or to /contact/?error=fields|check|send.
import { EmailMessage } from "cloudflare:email";

const SITE = __SITE__;
const HOST = __HOST__;
const TO = __TO__;
const FROM = __FROM__;
const NAME = __NAME__;

function back(path) {
  return new Response(null, { status: 303, headers: { Location: SITE + path, "Cache-Control": "no-store" } });
}

function oneLine(value, max) {
  return String(value || "").replace(/[\r\n\t]+/g, " ").replace(/[<>"\\]/g, "").trim().slice(0, max);
}

function b64(text) {
  const bytes = new TextEncoder().encode(text);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

function headerText(text) {
  // RFC 2047: plain ASCII as is, anything else as UTF-8 encoded words of at most 45 bytes each
  if (/^[\x20-\x7E]*$/.test(text)) return text;
  const words = [];
  let chunk = "";
  for (const ch of text) {
    if (new TextEncoder().encode(chunk + ch).length > 45) {
      words.push("=?UTF-8?B?" + b64(chunk) + "?=");
      chunk = "";
    }
    chunk += ch;
  }
  if (chunk) words.push("=?UTF-8?B?" + b64(chunk) + "?=");
  return words.join(" ");
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("This address only accepts the contact form at " + SITE + "/contact/.", {
        status: 405, headers: { Allow: "POST", "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
    }
    if (Number(request.headers.get("content-length") || "0") > 65536) return back("/contact/?error=fields"); // far more than the form can hold
    let form;
    try {
      form = await request.formData();
    } catch (err) {
      return back("/contact/?error=fields");
    }
    if (String(form.get("website") || "").trim()) return back("/contact/thanks/"); // honeypot field, hidden from people

    const name = oneLine(form.get("name"), 120);
    const email = oneLine(form.get("email"), 254);
    const topic = oneLine(form.get("topic"), 80);
    const message = String(form.get("message") || "").replace(/\r\n?/g, "\n").trim().slice(0, 5000);
    if (!name || !/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$/.test(email) || message.length < 2) {
      return back("/contact/?error=fields");
    }

    if (!env.TURNSTILE_SECRET) {
      console.log("contact form: the secret TURNSTILE_SECRET is not set");
      return back("/contact/?error=send");
    }
    const token = String(form.get("cf-turnstile-response") || "");
    if (!token) return back("/contact/?error=check");
    const check = new FormData();
    check.append("secret", env.TURNSTILE_SECRET);
    check.append("response", token);
    const ip = request.headers.get("CF-Connecting-IP");
    if (ip) check.append("remoteip", ip);
    let outcome = { success: false };
    try {
      const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: check });
      outcome = await res.json();
    } catch (err) {
      outcome = { success: false };
    }
    if (!outcome.success || (outcome.hostname && outcome.hostname !== HOST) || (outcome.action && outcome.action !== "contact")) {
      return back("/contact/?error=check");
    }

    const text = ["Name: " + name, "Email: " + email]
      .concat(topic ? ["Topic: " + topic] : [])
      .concat(["", message, "", "Sent from the contact form at " + HOST + "."])
      .join("\r\n");
    const raw = [
      "From: " + NAME + " <" + FROM + ">",
      "To: <" + TO + ">",
      "Reply-To: " + (/^[\x20-\x7E]*$/.test(name) ? "\"" + name + "\"" : headerText(name)) + " <" + email + ">",
      "Subject: " + headerText("Contact form" + (topic ? " (" + topic + ")" : "") + ": " + name.slice(0, 60)),
      "Date: " + new Date().toUTCString(),
      "Message-ID: <" + crypto.randomUUID() + "@" + HOST + ">",
      "MIME-Version: 1.0",
      "Content-Type: text/plain; charset=utf-8",
      "Content-Transfer-Encoding: base64",
      "",
      b64(text).replace(/.{1,76}/g, "$&\r\n"),
    ].join("\r\n");
    try {
      await env.SEND_EMAIL.send(new EmailMessage(FROM, TO, raw));
    } catch (err) {
      console.log("contact form: send failed: " + (err && err.message));
      return back("/contact/?error=send");
    }
    return back("/contact/thanks/");
  },
};
"""

CONTACT_WRANGLER = """// Wrangler configuration for the contact form Worker. Written by tools/build_public_site.py on every site build;
// edit the generator, not this file. Cloudflare Workers Builds deploys this folder to the Worker named below whenever it
// changes on main (Worker settings: root directory contact-worker, deploy command "npx wrangler deploy", build watch path
// contact-worker/*). The Turnstile secret key is the Worker secret TURNSTILE_SECRET, set in the dashboard; secrets are kept
// across deploys and never belong in this file.
__JSON__
"""

CONTACT_README = """# Contact form Worker

Written by tools/build_public_site.py on every site build; edit the generator, not these files.

The form at https://__HOST__/contact/ posts to __ROUTE__, which this Worker answers. It checks the Cloudflare Turnstile
token, emails the message through the Email Routing binding SEND_EMAIL to the verified destination address, and sends the
visitor back to /contact/thanks/ (or to /contact/?error=...).

Cloudflare Workers Builds deploys this folder to the Worker "__WORKER__" when anything in it changes on main
(root directory `contact-worker`, deploy command `npx wrangler deploy`, build watch path `contact-worker/*`).

One secret is set in the Cloudflare dashboard and never kept here: TURNSTILE_SECRET, the contact form widget's secret key
(Workers & Pages, __WORKER__, Settings, Variables and Secrets). Wrangler keeps it across deploys.
"""


def write_contact_worker():
    """Write <repo root>/contact-worker/ (src/index.js, wrangler.jsonc, README.md) for Cloudflare Workers Builds. True when written.
    With the contact form turned off (config "contact": false) nothing is written and an existing folder is left alone."""
    if not CONTACT:
        return False
    host = CONTACT["zone"]
    path = CONTACT.get("path") or "/api/contact"
    route = host + path
    cfg = {"name": CONTACT["worker"], "main": "src/index.js", "compatibility_date": CONTACT.get("compatibility_date") or "2026-09-30",
           "workers_dev": False, "preview_urls": False,
           "routes": [{"pattern": route, "zone_name": host}],
           "send_email": [{"name": "SEND_EMAIL", "destination_address": CONTACT["to"]}],
           "observability": {"enabled": True}}
    files = {
        os.path.join("src", "index.js"): (CONTACT_WORKER_JS.replace("__ROUTE__", route).replace("__SITE__", json.dumps("https://" + host))
                                          .replace("__HOST__", json.dumps(host)).replace("__TO__", json.dumps(CONTACT["to"]))
                                          .replace("__FROM__", json.dumps(CONTACT["from"])).replace("__NAME__", json.dumps(NAME))),
        "wrangler.jsonc": CONTACT_WRANGLER.replace("__JSON__", json.dumps(cfg, indent=2)),
        "README.md": CONTACT_README.replace("__HOST__", host).replace("__ROUTE__", route).replace("__WORKER__", CONTACT["worker"]),
    }
    folder = os.path.join(ROOT, "contact-worker")
    for rel, text in files.items():
        full = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
    return True


def write_episode_function():
    """Write (or remove) the Netlify function behind /api/episode/<date>. Returns True when it is written."""
    target = os.path.join(ROOT, "netlify", "functions", "episode.mjs")
    if not POD:
        if os.path.exists(target):
            os.remove(target)
        return False
    os.makedirs(os.path.dirname(target), exist_ok=True)
    src = (EPISODE_FN.replace("__FEED__", json.dumps(POD["rss"]))
           .replace("__TITLES__", json.dumps(POD["episode_titles"]))
           .replace("__LETTER__", json.dumps(POD.get("letter_title_prefix") or "Friday Letter"))
           .replace("__SPECIAL__", json.dumps(POD.get("special_title_prefix") or "Special Topic")))
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    return True

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
    """kind: 'posts', 'letters' or 'specials'. Returns slug -> (site path or https url, alt, raster?).

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
SPECIAL_IMG = collect_images("specials", special_pages)
EXPLAINER_IMG = collect_images("explainers", [(x["slug"], x) for x in EXPLAINERS])  # 2.16

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

# 2.16: "Share story". The share sheet where the browser has one, else copy the address; without JavaScript, an email.
SHARE_ICON = ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">'
              '<path d="M12 15V3.5M7.5 8L12 3.5 16.5 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
              '<path d="M5 11.5V19a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
SHARE_SCRIPT = ('<script>(function(){if(window.__pitlShare)return;window.__pitlShare=1;document.addEventListener("click",function(e){'
                'var a=e.target&&e.target.closest?e.target.closest("a.share-link"):null;if(!a)return;'
                'var u=a.getAttribute("data-share-url")||location.href,t=a.getAttribute("data-share-title")||document.title,'
                'n=a.parentNode&&a.parentNode.querySelector(".share-note");'
                'function say(s){if(!n)return;n.textContent=s;clearTimeout(n._t);n._t=setTimeout(function(){n.textContent=""},3000);}'
                'if(navigator.share){e.preventDefault();navigator.share({title:t,url:u}).catch(function(){});return;}'
                'if(navigator.clipboard&&window.isSecureContext){e.preventDefault();'
                'navigator.clipboard.writeText(u).then(function(){say("Link copied")},function(){location.href=a.href;});}'
                '});})();</script>')

def share_html(path, title):
    url = absurl(path)
    title = plain(title) or NAME
    mail = "mailto:?subject=%s&body=%s" % (urllib.parse.quote(title), urllib.parse.quote(title + "\n\n" + url))
    return ('<div class="share-row"><a class="btn ghost small share-link" href="%s" data-share-url="%s" data-share-title="%s">%sShare story</a>'
            '<span class="share-note" role="status" aria-live="polite"></span></div>%s' % (esc(mail), esc(url), esc(title), SHARE_ICON, SHARE_SCRIPT))

def list_thumb(img_map, slug, href, k):
    """The picture beside an entry in a list page (/letters/, /specials/, /posts/, /explainers/), linked to the piece."""
    if slug not in img_map:
        return ""
    src, alt, _ = img_map[slug]
    return ('<a class="thumb" href="%s" tabindex="-1" aria-hidden="true"><img src="%s" alt="%s" width="1200" height="630" decoding="async"%s></a>'
            % (href, esc(src), esc(alt), ' loading="lazy"' if k > 1 else ""))

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
    body.append(share_html(post_url(slug0), p0.get("headline") or "Daily post, " + fmt(p0.get("date"))))
    body.append(post_body(p0, fig=post_figure(slug0), under_fig="" if p0.get("baseline") else episode_block(p0.get("date"))))
    body.append('<div class="more-row"><a class="btn ghost small" href="%s">Link to this post</a><a class="btn ghost small" href="/posts/">All posts</a><a class="btn ghost small" href="/where-things-stand/">Where things stand</a>%s</div></article>'
                % (post_url(slug0), '<a class="btn ghost small" href="/specials/">Special topics</a>' if specials else ""))
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
if PATIENTS:
    px = PATIENTS[0]
    body.append('<div class="panel-head" style="margin-top:34px"><h2 style="font-size:1.3rem">For patients</h2><a class="sub" href="/patients/">all letters</a></div>')
    body.append('<ul class="recent"><li><span class="when">%s</span><a href="%s">%s</a></li></ul>' % (esc(fmt(px["weekOf"])), patient_url(px["weekOf"]), esc(px.get("headline") or "")))
REF_LINKS = [(p_, l_) for p_, l_, have in (("/law-map/", "AI health law map", LAWS), ("/rhtp/", "Rural Health Transformation Program tracker", RHTP), ("/explainers/", "Explainers", EXPLAINERS)) if have]
if REF_LINKS:
    body.append('<div class="panel-head" style="margin-top:34px"><h2 style="font-size:1.3rem">Guides and trackers</h2></div><div class="ref-row">%s</div>'
                % "".join('<a class="btn ghost small" href="%s">%s</a>' % (p_, esc(l_)) for p_, l_ in REF_LINKS))
home_ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE, "description": config["description"], "inLanguage": "en-US", "publisher": PUBLISHER}]
HASH_REDIRECT = ('<script>(function(){var h=location.hash.replace(/^#/,"");if(!h)return;var map=%s;if(map[h]){location.replace(map[h]);return;}'
                 'var m=/^post-(\\d{4}-\\d{2}-\\d{2})-\\d+$/.exec(h);if(m){location.replace("/posts/"+m[1]+"/");return;}'
                 'if(h.indexOf("letter-")===0){location.replace("/letters/"+h.slice(7)+"/");return;}'
                 'if(h.indexOf("special-")===0){location.replace("/specials/"+h.slice(8)+"/");}})();</script>' % json.dumps(HASH_MAP))
page("/", PAGE_TITLE + ": " + config["tagline"], config["description"], '<section class="panel">' + "".join(body) + "</section>", active="/", jsonld=home_ld, head_extra=HASH_REDIRECT)
urls.append(("/", LAST_UPDATED, "daily", "1.0"))

# ------------------------------------------------------------------ daily posts
def entry_page(kind, path, crumbs, headline, desc, date, article_html, older, newer, extra_ld=None, image=None, image_alt=None, unsigned=False, tail=None):
    ld, crumb_html = breadcrumbs(crumbs)
    lds = [article_ld(kind, absurl(path), headline, desc, date, image, unsigned=unsigned), ld] + ([extra_ld] if extra_ld else [])
    body = crumb_html + article_html + pager(older, newer) + (subscribe_box() if tail is None else tail)
    page(path, headline, desc, '<section class="panel">' + body + "</section>", active="/%s/" % path.split("/")[1], kind="article", jsonld=lds, published=iso_dt(date), modified=iso_dt(date), image=image, image_alt=image_alt, unsigned=unsigned)

for i, (slug, p) in enumerate(post_pages):
    path = post_url(slug)
    headline = p.get("headline") or "Daily post, " + fmt(p.get("date"))
    desc = describe(p.get("intro") or p.get("summary") or [p.get("dek") or headline])
    art = ['<article class="post"><div class="post-date"><time datetime="%s">%s</time>%s</div><h1 class="headline">%s</h1>' % (esc(p.get("date", "")), esc(fmt(p.get("date"))), " · Pinned" if p.get("baseline") else "", esc(headline))]
    art.append(share_html(path, headline))
    art.append(post_body(p, anchors=True, fig=post_figure(slug), under_fig="" if p.get("baseline") else episode_block(p.get("date"))))
    art.append("</article>")
    older = (post_pages[i + 1][1].get("headline", ""), post_url(post_pages[i + 1][0])) if i + 1 < len(post_pages) else None
    newer = (post_pages[i - 1][1].get("headline", ""), post_url(post_pages[i - 1][0])) if i > 0 else None
    og_i, og_alt = og_for(POST_IMG, slug)
    entry_page("NewsArticle", path, [(NAME, "/"), ("Daily posts", "/posts/"), (fmt(p.get("date")), None)], headline, desc, p.get("date"), "".join(art), older, newer, image=og_i, image_alt=og_alt)
    urls.append((path, p.get("date") or LAST_UPDATED, "weekly" if i else "daily", "0.8" if i < 7 else "0.6"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Daily posts</h1><span class="sub">newest first</span></div>',
        '<p class="lead">One post every morning: what happened in AI and medicine the day before, written as straight news with every source linked.</p>']
if post_pages:
    body.append('<ul class="letter-list post-list">')
    for k, (slug, p) in enumerate(post_pages):
        thumb = list_thumb(POST_IMG, slug, post_url(slug), k)
        body.append('<li%s>%s<div class="txt"><span class="when">%s</span><a class="t" href="%s">%s%s</a></div></li>' % (
            "" if thumb else ' class="no-thumb"', thumb, esc(fmt(p.get("date"))), post_url(slug), "Pinned. " if p.get("baseline") else "", esc(p.get("headline", ""))))
    body.append("</ul>")
else:
    body.append('<p class="empty">No posts yet.</p>')
body.append('<p class="lead" style="margin-top:22px">The same items sorted by kind: <a href="/topics/regulation/">regulation</a>, <a href="/topics/deployment/">deployment</a>, <a href="/topics/evidence/">evidence</a>, <a href="/topics/money/">money</a>, <a href="/topics/workforce/">workforce</a>, <a href="/topics/incident/">incidents</a>.</p>')
page("/posts/", "Daily posts", "Every daily post from %s, newest first: AI in medicine as straight news, with the sources linked." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/posts/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Daily posts", "url": absurl("/posts/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/posts/", LAST_UPDATED, "daily", "0.9"))

# ------------------------------------------------------------------ Friday letters
def letter_record(slug, w):
    """The letter as plain text, for the podcast pipeline that reads it aloud (links reduced to their words)."""
    friday = ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", w.get("weekOf") or "")
    if m:
        import datetime as _dt
        fd = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) + _dt.timedelta(days=4)
        friday = fd.isoformat()
    img = LETTER_IMG.get(slug)
    return {
        "weekOf": w.get("weekOf") or "",
        "friday": friday,
        "dateRange": w.get("dateRange") or "",
        "headline": plain(w.get("headline") or ""),
        "dek": plain(w.get("dek") or ""),
        "url": absurl(letter_url(slug)),
        "image": (img[0] if img and img[0].startswith("https://") else absurl(img[0])) if img else None,
        "image_alt": img[1] if img else None,
        "body": [plain(x) for x in (w.get("body") or w.get("summary") or []) if x],
        "outlook": [plain(x) for x in (w.get("outlook") or []) if x],
        "top": [{"title": plain(x.get("title") or ""), "body": plain(x.get("body") or ""), "url": x.get("url") or ""}
                for x in (w.get("top") or []) if isinstance(x, dict)],
    }

for i, (slug, w) in enumerate(letter_pages):
    path = letter_url(slug)
    headline = w.get("headline") or "The Friday letter, " + (w.get("dateRange") or fmt(w.get("weekOf")))
    desc = describe([w.get("dek")] if w.get("dek") else (w.get("body") or [headline]))
    art = ['<article class="post letter"><div class="post-date">The Friday letter · <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(w.get("weekOf", "")), esc(w.get("dateRange") or fmt(w.get("weekOf"))), esc(headline))]
    if w.get("dek"):
        art.append('<p class="standfirst">%s</p>' % rich(w["dek"]))
    art.append(share_html(path, headline))
    art.append(letter_figure(slug))
    art.append(letter_audio_block(w.get("weekOf")))
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
    letter_json = letter_record(slug, w)
    write(path + "letter.json", json.dumps(letter_json, ensure_ascii=False, indent=1) + "\n")
    if i == 0:
        write("/letters/latest.json", json.dumps(letter_json, ensure_ascii=False, indent=1) + "\n")
    entry_page("Article", path, [(NAME, "/"), ("Friday letter", "/letters/"), (w.get("dateRange") or fmt(w.get("weekOf")), None)], headline, desc, w.get("weekOf"), "".join(art), older, newer, image=og_i, image_alt=og_alt, unsigned=True)
    urls.append((path, w.get("weekOf") or LAST_UPDATED, "monthly", "0.8"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">The Friday letter</h1><a class="sub" href="%s" target="_blank" rel="noopener">archive on Substack</a></div>' % esc(SUBSTACK),
        '<p class="lead">Once a week, the version worth keeping: the week\'s developments, why they matter, and specific recommendations. It goes to subscribers by email on Friday mornings and lands here the same day.</p>']
if letter_pages:
    body.append('<ul class="letter-list">')
    for k, (slug, w) in enumerate(letter_pages):
        thumb = ""
        if slug in LETTER_IMG:
            src, alt, _ = LETTER_IMG[slug]
            thumb = ('<a class="thumb" href="%s" tabindex="-1" aria-hidden="true"><img src="%s" alt="%s" width="1200" height="630" decoding="async"%s></a>'
                     % (letter_url(slug), esc(src), esc(alt), ' loading="lazy"' if k > 1 else ""))
        body.append('<li%s>%s<div class="txt"><span class="when">%s</span><a class="t" href="%s">%s</a>%s</div></li>' % (
            "" if thumb else ' class="no-thumb"', thumb, esc(w.get("dateRange") or fmt(w.get("weekOf"))), letter_url(slug),
            esc(w.get("headline") or "The Friday letter"), ('<p class="d">%s</p>' % esc(plain(w["dek"]))) if w.get("dek") else ""))
    body.append("</ul>")
else:
    body.append('<p class="empty">The first letter is on its way.</p>')
body.append(subscribe_box())
page("/letters/", "The Friday letter", "The weekly letter from %s: the week's developments in AI and medicine, why they matter, and specific recommendations for physicians." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/letters/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "The Friday letter", "url": absurl("/letters/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/letters/", LAST_UPDATED, "weekly", "0.9"))

# ------------------------------------------------------------------ special topics
def special_record(slug, sp):
    """The special as plain text, for the podcast pipeline that reads it aloud (links reduced to their words; pull
    quotes left out because they repeat the text; subheadings kept as their own lines)."""
    img = SPECIAL_IMG.get(slug)
    body = []
    for b in sp.get("blocks") or []:
        kind = b.get("type")
        if kind == "pull":
            continue
        line = plain(((b.get("lead") or "") + " " + (b.get("text") or "")).strip() if kind == "step" else (b.get("text") or ""))
        if line:
            body.append(line)
    return {
        "slug": slug,
        "date": sp.get("date") or "",
        "headline": plain(sp.get("title") or ""),
        "dek": plain(sp.get("dek") or ""),
        "url": absurl(special_url(slug)),
        "unsigned": bool(sp.get("unsigned")),
        "image": (img[0] if img and img[0].startswith("https://") else absurl(img[0])) if img else None,
        "image_alt": img[1] if img else None,
        "body": body,
        "top": [{"title": plain(x.get("title") or ""), "body": plain(x.get("body") or ""), "url": x.get("url") or ""}
                for x in (sp.get("top") or []) if isinstance(x, dict)],
    }

for i, (slug, sp) in enumerate(special_pages):
    path = special_url(slug)
    title = sp.get("title") or "Special topic"
    desc = describe([sp.get("dek")] if sp.get("dek") else [b.get("text", "") for b in (sp.get("blocks") or []) if b.get("type") == "p"][:1] or [title])
    art = ['<article class="post special"><div class="post-date">Special topic · <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(sp.get("date", "")), esc(fmt(sp.get("date"))), esc(title))]
    if sp.get("dek"):
        art.append('<p class="standfirst">%s</p>' % rich(sp["dek"]))
    art.append(share_html(path, title))
    art.append(figure_html(SPECIAL_IMG, slug, "letter-art"))
    art.append(special_audio_block(slug))
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
    if sp.get("top"):
        art.append('<div class="section-label details-label">SOURCE MATERIAL</div>' + render_items(sp["top"]))
    if sp.get("substackUrl"):
        art.append('<p class="mono" style="margin-top:18px">%s</p>' % ext_link("Read this on Substack", sp["substackUrl"]))
    art.append("</article>")
    older = (special_pages[i + 1][1].get("title", ""), special_url(special_pages[i + 1][0])) if i + 1 < len(special_pages) else None
    newer = (special_pages[i - 1][1].get("title", ""), special_url(special_pages[i - 1][0])) if i > 0 else None
    og_i, og_alt = og_for(SPECIAL_IMG, slug)
    write(path + "special.json", json.dumps(special_record(slug, sp), ensure_ascii=False, indent=1) + "\n")
    entry_page("Article", path, [(NAME, "/"), ("Special topics", "/specials/"), (title, None)], title, desc, sp.get("date"), "".join(art), older, newer,
               image=og_i, image_alt=og_alt, unsigned=bool(sp.get("unsigned")))
    urls.append((path, sp.get("date") or LAST_UPDATED, "monthly", "0.8"))

body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Special topics</h1><span class="sub">one question, worked all the way through</span></div>',
        '<p class="lead">Longer pieces on a single question physicians keep asking, argued from the evidence, with what to do about it. Each one also goes out on Substack.</p>']
if special_pages:
    body.append('<ul class="letter-list">')
    for k, (slug, sp) in enumerate(special_pages):
        thumb = ""
        if slug in SPECIAL_IMG:
            src, alt, _ = SPECIAL_IMG[slug]
            thumb = ('<a class="thumb" href="%s" tabindex="-1" aria-hidden="true"><img src="%s" alt="%s" width="1200" height="630" decoding="async"%s></a>'
                     % (special_url(slug), esc(src), esc(alt), ' loading="lazy"' if k > 1 else ""))
        body.append('<li%s>%s<div class="txt"><span class="when">%s</span><a class="t" href="%s">%s</a>%s</div></li>' % (
            "" if thumb else ' class="no-thumb"', thumb, esc(fmt(sp.get("date"))), special_url(slug),
            esc(sp.get("title") or "Special topic"), ('<p class="d">%s</p>' % esc(plain(sp["dek"]))) if sp.get("dek") else ""))
    body.append("</ul>")
else:
    body.append('<p class="empty">The first special topic is on its way.</p>')
page("/specials/", "Special topics", "Long pieces from %s on the questions physicians keep asking about AI, argued from the evidence, with what to do about it." % NAME, '<section class="panel">' + "".join(body) + "</section>", active="/specials/",
     jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Special topics", "url": absurl("/specials/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
urls.append(("/specials/", LAST_UPDATED, "weekly", "0.8"))

# ------------------------------------------------------------------ standing references (2.12): law map, program tracker, explainers, patient letters
TILE_ROWS = ["AK . . . . . . . . . ME", ". . . . . . . . . VT NH", "WA ID MT ND MN IL WI MI NY RI MA", "OR NV WY SD IA IN OH PA NJ CT .",
             "CA UT CO NE MO KY WV VA MD DE .", ". AZ NM KS AR TN NC SC . . .", ". . . OK LA MS AL GA . . .", "HI . . TX . . . . FL . ."]
TILES = {}
for _r, _row in enumerate(TILE_ROWS):
    for _c, _code in enumerate(_row.split()):
        if _code != ".":
            TILES[_code] = (_c + 1, _r + 1)
LAW_STATUS = {"introduced": "Introduced", "passed": "Passed", "enacted": "Enacted", "effective": "In force", "failed": "Failed", "blocked": "Blocked"}
LAW_ORDER = {"effective": 0, "enacted": 1, "passed": 2, "introduced": 3, "blocked": 4, "failed": 5}
LAW_KIND = {"law": "Law", "rule": "Rule", "policy": "Policy", "guidance": "Guidance", "order": "Executive order"}
# 2.13: a federal entry's status label depends on its kind ("*": any other kind); a status or kind not listed falls back to LAW_STATUS
FED_STATUS = {"introduced": {"rule": "Proposed", "guidance": "Draft", "policy": "Proposed", "law": "Introduced"},
              "enacted": {"rule": "Final", "law": "Enacted", "*": "Issued"},
              "effective": {"guidance": "Final", "order": "In effect", "policy": "In effect", "law": "In force", "rule": "In force"},
              "failed": {"order": "Revoked", "guidance": "Withdrawn", "rule": "Withdrawn", "law": "Failed", "policy": "Failed"}}
TODAY_ISO = LAST_UPDATED[:10] if _iso(LAST_UPDATED[:10]) else datetime.date.today().isoformat()
TODAY_D = datetime.date.fromisoformat(TODAY_ISO)
LLMS_EXTRA = ""
EXP_COUNTS = {"laws": 0, "states": 0, "federal": 0, "reviewed_none": 0, "rhtp": 0, "explainers": 0, "patients": 0}
NUM_WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def join_and(bits):
    bits = [b for b in bits if b]
    if len(bits) < 2:
        return "".join(bits)
    return ", ".join(bits[:-1]) + " and " + bits[-1]


def cat_lower(label):
    return label[:1].lower() + label[1:]


def is_fed(e):
    return e.get("state") == "US"


def cat_labels(e):
    """The category labels an entry uses: the eight federal ones for "US", the five state ones otherwise."""
    return FED_CAT_LABEL if is_fed(e) else LAW_CAT_LABEL


def law_status_label(e):
    st = (e.get("status") or "").lower()
    if is_fed(e):
        by_kind = FED_STATUS.get(st, {})
        kind = (e.get("kind") or "law").lower()
        if kind in by_kind or "*" in by_kind:
            return by_kind.get(kind, by_kind.get("*"))
    if st == "introduced" and (e.get("kind") or "").lower() == "rule":
        return "Proposed"
    return LAW_STATUS.get(st, st.capitalize() or "Status unknown")


def law_anchor(e):
    return "law-" + slugify(e.get("id") or e.get("name"))


def law_cats(e):
    labels = cat_labels(e)
    also = e.get("also") if isinstance(e.get("also"), list) else []
    return [e.get("category")] + [c for c in also if isinstance(c, str) and c in labels and c != e.get("category")]


def _clauses(*parts):
    """Date-line clauses joined with semicolons, the first capitalized; missing ones are left out."""
    s = "; ".join(p for p in parts if p)
    return s[:1].upper() + s[1:]


def fed_law_dates(e):
    """The date line under a federal entry's name."""
    st, kind = (e.get("status") or "").lower(), (e.get("kind") or "law").lower()
    signed_iso = e["signed"] if _iso(e.get("signed")) else ""
    eff_iso = e["effective"] if _iso(e.get("effective")) else ""
    signed, eff, ahead = fmt(signed_iso), fmt(eff_iso), eff_iso > TODAY_ISO
    if st == "effective":
        if kind == "guidance":
            return ("Issued %s" % signed) if signed else "Final guidance"
        if kind == "order":
            return ("Signed %s" % signed) if signed else ""
        if kind == "policy":
            return ("In effect since %s" % eff) if eff else (("Issued %s" % signed) if signed else "")
        s = ("In force since %s" % eff) if eff else "In force"
        return s + ((" (%s %s)" % ("published" if kind == "rule" else "signed", signed)) if signed and signed_iso != eff_iso else "")
    if st == "enacted":
        takes = (("takes effect %s" if ahead else "took effect %s") % eff) if eff else ""
        if kind == "rule":
            return _clauses(("Final rule published %s" % signed) if signed else "Final rule", takes)
        if kind == "law":
            return _clauses(("Signed %s" % signed) if signed else "", (("main duties begin %s" if ahead else "main duties began %s") % eff) if eff else "")
        return _clauses(("Issued %s" % signed) if signed else "", takes)
    if st == "passed":
        return "Passed both chambers of Congress; awaiting the president"
    if st == "introduced":
        first = {"rule": ("Proposed rule published %s" % signed) if signed else "Proposed rule",
                 "guidance": ("Draft issued %s" % signed) if signed else "Draft guidance",
                 "law": "Bill in Congress",
                 "policy": ("Proposed %s" % signed) if signed else ""}.get(kind, "")
        return _clauses(first, ("would take effect %s" % eff) if eff else "")
    if st == "failed":
        return {"order": "Revoked", "guidance": "Withdrawn", "rule": "Withdrawn"}.get(kind, "Failed or withdrawn")
    if st == "blocked":
        return "Blocked by a court"
    return ""


def law_dates(e):
    if is_fed(e):
        return fed_law_dates(e)
    st, kind = (e.get("status") or "").lower(), (e.get("kind") or "law").lower()
    signed = e.get("signed") if _iso(e.get("signed")) else ""
    eff = e.get("effective") if _iso(e.get("effective")) else ""
    verb = {"rule": "adopted", "policy": "issued"}.get(kind, "signed")
    if st == "effective":
        s = ("In force since %s" % fmt(eff)) if eff else "In force"
        return s + ((" (%s %s)" % (verb, fmt(signed))) if signed and signed != eff else "")
    if st == "enacted":
        s = ("%s %s" % (verb.capitalize(), fmt(signed))) if signed else verb.capitalize()
        if eff:
            return s + ("; main duties begin %s" % fmt(eff) if eff > TODAY_ISO else "; main duties began %s" % fmt(eff))
        return s + "; main duties not yet in force"
    if st == "passed":
        return "Passed the legislature; awaiting the governor" + (("; would take effect %s" % fmt(eff)) if eff else "")
    if st == "introduced":
        return ("Proposed rule" if kind == "rule" else "Bill in the legislature") + (("; would take effect %s" % fmt(eff)) if eff else "")
    if st == "blocked":
        return "Blocked" + (("; had been due to take effect %s" % fmt(eff)) if eff else "")
    if st == "failed":
        return "Failed or withdrawn"
    return ""


def law_card(e):
    st = (e.get("status") or "").lower()
    kind = (e.get("kind") or "law").lower()
    out = ['<article class="law" id="%s">' % esc(law_anchor(e)),
           '<div class="law-top"><span class="lstat st-%s">%s</span><span class="law-kind">%s</span></div>'
           % (esc(slugify(st)), esc(law_status_label(e)), esc(LAW_KIND.get(kind, kind.capitalize()))),
           '<h3 class="law-name">%s</h3>' % esc(e.get("name") or e.get("id"))]
    dl = law_dates(e)
    if dl:
        out.append('<div class="law-dates">%s</div>' % esc(dl))
    if e.get("summary"):
        out.append('<p class="law-sum">%s</p>' % rich(e["summary"]))
    if e.get("physician_read"):
        out.append('<p class="law-read"><strong>Physician read.</strong> %s</p>' % rich(e["physician_read"]))
    meta = []
    if e.get("applies_to"):
        meta.append("<strong>Applies to:</strong> %s" % rich(e["applies_to"]))
    labels = cat_labels(e)
    also = [labels[c] for c in law_cats(e)[1:]]
    if also:
        meta.append("<strong>Also touches:</strong> %s" % esc("; ".join(also)))
    if meta:
        out.append('<p class="law-meta">%s</p>' % "<br>".join(meta))
    srcs = e.get("sources") if isinstance(e.get("sources"), list) else []
    # 2.13.1: labels such as "NAIC adoption map, Aug. 31, 2026" carry commas, so such a list is separated by semicolons
    comma = any("," in str(x.get("label") or "") for x in srcs if isinstance(x, dict))
    out.append(sources_line("law-src", srcs, sep="; " if comma else ", "))
    if e.get("notes"):
        out.append('<p class="law-notes"><strong>Notes:</strong> %s</p>' % rich(e["notes"]))
    if e.get("correction"):
        out.append('<p class="law-notes"><strong>Correction:</strong> %s</p>' % rich(e["correction"]))
    if _iso(e.get("checked")):
        out.append('<div class="law-checked">Checked against its sources <time datetime="%s">%s</time></div>' % (esc(e["checked"]), esc(fmt(e["checked"]))))
    out.append("</article>")
    return "".join(out)


def state_summary(entries):
    live = [e for e in entries if (e.get("status") or "") != "failed"]
    count = {}
    for e in live:
        count[e.get("status")] = count.get(e.get("status"), 0) + 1
    bits = []
    if count.get("effective"):
        bits.append("%d in force" % count["effective"])
    if count.get("enacted"):
        effs = sorted(set(e["effective"] for e in live if e.get("status") == "enacted" and _iso(e.get("effective")) and e["effective"] > TODAY_ISO))
        bits.append("%d enacted and not yet in force%s" % (count["enacted"], (" (main duties begin %s)" % join_and([fmt(x) for x in effs])) if effs else ""))
    if count.get("passed"):
        bits.append("%d awaiting the governor" % count["passed"])
    rules = sum(1 for e in live if e.get("status") == "introduced" and (e.get("kind") or "") == "rule")
    bills = count.get("introduced", 0) - rules
    if bills:
        bits.append("%d %s in the legislature" % (bills, "bill" if bills == 1 else "bills"))
    if rules:
        bits.append("%d proposed %s" % (rules, "rule" if rules == 1 else "rules"))
    if count.get("blocked"):
        bits.append("%d blocked" % count["blocked"])
    n = len(live)
    s = "%d %s on the map" % (n, "entry" if n == 1 else "entries")
    return s + (": " + join_and(bits) + "." if bits else ".")


def fed_summary(entries):
    """The federal page's standfirst: its entries counted by status, failed ones left out."""
    live = [e for e in entries if (e.get("status") or "") != "failed"]
    count = {}
    for e in live:
        count[e.get("status")] = count.get(e.get("status"), 0) + 1
    bits = []
    if count.get("effective"):
        bits.append("%d in force or in effect" % count["effective"])
    if count.get("enacted"):
        effs = sorted(set(e["effective"] for e in live if e.get("status") == "enacted" and _iso(e.get("effective")) and e["effective"] > TODAY_ISO))
        bits.append("%d final or enacted and not yet in force%s" % (count["enacted"], (" (main duties begin %s)" % join_and([fmt(x) for x in effs])) if effs else ""))
    if count.get("passed"):
        bits.append("%d passed by Congress and awaiting the president" % count["passed"])
    for kind, one, many in (("rule", "proposed rule", "proposed rules"), ("guidance", "draft guidance document", "draft guidance documents"), ("law", "bill in Congress", "bills in Congress")):
        n = sum(1 for e in live if e.get("status") == "introduced" and (e.get("kind") or "law").lower() == kind)
        if n:
            bits.append("%d %s" % (n, one if n == 1 else many))
    if count.get("blocked"):
        bits.append("%d blocked by a court" % count["blocked"])
    n = len(live)
    s = "%d %s on the map" % (n, "entry" if n == 1 else "entries")
    return s + (": " + join_and(bits) + "." if bits else ".")


def law_line(e, when):
    """One entry in a list on the /law-map/ page."""
    return ('<li><span class="when">%s</span><div><a href="%s#%s">%s</a><div class="d">%s · %s · %s</div></div></li>'
            % (esc(when), law_state_url(e["state"]), esc(law_anchor(e)), esc(e.get("name") or e.get("id")), esc("Federal" if is_fed(e) else STATE_NAME[e["state"]]),
               esc(cat_labels(e)[e["category"]]), esc(law_status_label(e))))


def law_is_update(e):
    """True when a recent entry shows as "Updated" rather than "Added" on /law-map/."""
    return bool(e.get("changed") and e.get("changed") != e.get("added"))


def law_bulk_line(d, entries):
    """One line on /law-map/ for the many entries added on one day."""
    states = sorted(set(e["state"] for e in entries if not is_fed(e)))
    fed = any(is_fed(e) for e in entries)
    if states:
        main = "%d entries added in %d %s%s" % (len(entries), len(states), "state" if len(states) == 1 else "states", " and the federal section" if fed else "")
        see = "See each state's page, or the federal page." if fed else "See each state's page."
    else:
        main = "%d entries added in the federal section" % len(entries)
        see = "See the federal page."
    return '<li><span class="when">%s</span><div><span class="lm-bulk">%s</span><div class="d">%s</div></div></li>' % (esc("Added " + fmt(d)), esc(main), esc(see))


def law_dates_ahead(live, labels):
    """The "Dates ahead" list on a state or the federal page."""
    upcoming = [e for e in live if e.get("status") in ("enacted", "passed") and _iso(e.get("effective")) and e["effective"] > TODAY_ISO]
    if not upcoming:
        return ""
    return '<h2 class="lm-h">Dates ahead</h2><ul class="archive">%s</ul>' % "".join(
        '<li><span class="when">%s</span><div><a href="#%s">%s</a><div class="d">%s</div></div></li>'
        % (esc(fmt(e["effective"])), esc(law_anchor(e)), esc(e.get("name") or ""), esc(labels[e["category"]])) for e in sorted(upcoming, key=lambda e: e["effective"]))


def law_sections(live, cats, review, fallback):
    """The category chips and one section per category on a state or the federal page. A category with no entries of its own
    shows the review's "empty" text for it, if any; otherwise, when nothing at all is in the section, the fallback text."""
    empty = (review or {}).get("empty") or {}
    labels = {k: l for k, l, _ in cats}
    out = ['<nav class="law-toc" aria-label="Categories">%s</nav>' % "".join('<a class="chip" href="#%s">%s</a>' % (k, esc(l)) for k, l, _ in cats)]
    for key, label, blurb in cats:
        main = [e for e in live if e.get("category") == key]
        also = [e for e in live if e.get("category") != key and key in law_cats(e)]
        out.append('<section class="law-cat" id="%s"><h2>%s</h2><p class="law-cat-note">%s</p>' % (key, esc(label), esc(blurb)))
        for e in main:
            try:
                out.append(law_card(e))
            except Exception as ex:
                print("warning: law map entry %s left out: %s" % (e.get("id"), ex), file=sys.stderr)
        said = "" if main else (empty.get(key) or "").strip()
        if said:
            out.append('<p class="empty">%s</p>' % rich(said))
        if also:
            out.append('<p class="law-also">Also relevant here: %s.</p>' % "; ".join(
                '<a href="#%s">%s</a> (under %s)' % (esc(law_anchor(e)), esc(e.get("name") or ""), esc(cat_lower(labels[e["category"]]))) for e in also))
        if not main and not also and not said:
            out.append('<p class="empty">%s</p>' % esc(fallback))
        out.append("</section>")
    return "".join(out)


def law_failed_section(failed, title):
    """The last section of a state or the federal page: entries that failed, were withdrawn or were revoked."""
    cards = []
    for e in failed:
        try:
            cards.append(law_card(e))
        except Exception as ex:
            print("warning: law map entry %s left out: %s" % (e.get("id"), ex), file=sys.stderr)
    return '<section class="law-cat" id="failed"><h2>%s</h2>%s</section>' % (esc(title), "".join(cards)) if cards else ""


LAW_FOOT = ('<p class="law-foot">%sGeneral information, not legal advice. <a href="/law-map/">How the map works</a>, and the '
            '<a href="/law-map/laws.json">data</a>.</p>')
FED_LINE = '<p class="law-also law-fed">Federal law also applies in every state: see <a href="%s">federal law and policy</a>.</p>' % FED_URL
# 2.13's few extra styles, put in the head of a law map page only when the page uses them, so every other page is unchanged
LAW_CSS = (("lm-fed", ".lm-fed { margin: 16px 0 0; padding: 10px 14px; background: var(--surface); border: 1px solid var(--rule); "
                      "border-radius: 10px; font-size: 0.95rem; color: var(--ink-2); } .lm-fed a { font-weight: 600; }"),
           ("lm-bulk", ".archive .lm-bulk { font-family: var(--display); font-weight: 600; font-size: 1.08rem; line-height: 1.3; color: var(--ink); }"),
           ("law-intro", ".lawstate .law-intro { margin-top: 12px; }"),
           ("law-fed", ".lawstate .law-fed { margin-top: 26px; } .lawstate .law-fed + .law-foot { margin-top: 8px; }"))


def law_css(body):
    rules = [css for cls, css in LAW_CSS if re.search(r'class="(?:[^"]* )?%s[ "]' % re.escape(cls), body)]
    return "<style>%s</style>" % " ".join(rules) if rules else ""


def law_checked_foot(ents):
    checked = max([e.get("checked") for e in ents if _iso(e.get("checked"))] or [""])
    return LAW_FOOT % (("Most recently checked %s. " % fmt(checked)) if checked else "")


def law_sorted(entries):
    return sorted(entries, key=lambda e: (LAW_ORDER.get(e.get("status"), 9), e.get("effective") or "", e.get("name") or ""))


LAWMAP_SCRIPT = ('<script>(function(){var g=document.querySelector(".lawmap-filter");if(!g)return;g.hidden=false;'
                 'var bs=g.querySelectorAll("button"),ts=document.querySelectorAll(".tilemap .tile[data-all]"),cap=document.getElementById("lawmap-cap");'
                 'function lv(n){return n>=4?3:n>=2?2:n>=1?1:0}'
                 'for(var i=0;i<bs.length;i++){bs[i].addEventListener("click",function(){var c=this.getAttribute("data-cat");'
                 'for(var j=0;j<bs.length;j++){bs[j].setAttribute("aria-pressed",bs[j]===this?"true":"false")}'
                 'for(var k=0;k<ts.length;k++){var n=+(ts[k].getAttribute("data-"+c)||0);ts[k].className="tile lv-"+lv(n)}'
                 'if(cap){cap.textContent=c==="all"?"Shaded by the number of laws and rules enacted or in force.":'
                 '"Shaded by the number enacted or in force in one category: "+this.textContent+"."}})}})();</script>')


def build_federal_page(entries, review):
    """/law-map/federal/: every federal entry, by category, with the counts, the dates ahead and the withdrawn ones last."""
    ents = law_sorted(entries)
    live = [e for e in ents if e.get("status") != "failed"]
    failed = [e for e in ents if e.get("status") == "failed"]
    summary = fed_summary(ents)
    crumb_ld, crumb_html = breadcrumbs([(NAME, "/"), ("Law map", "/law-map/"), ("Federal", None)])
    art = [crumb_html, '<article class="post lawstate"><div class="post-date">AI health law map</div>',
           '<h1 class="headline">Federal: AI health law and policy</h1>', '<p class="standfirst">%s</p>' % esc(summary),
           '<p class="lm-note law-intro">The federal section records statutes, final and proposed rules, agency guidance, executive orders and CMS programs '
           'that govern or directly shape the use of AI in health care, and lists a bill in Congress once it has passed a committee.</p>']
    note = ((review or {}).get("note") or "").strip()
    if note:
        art.append('<p class="lm-note">%s</p>' % rich(note))
    art.append(law_dates_ahead(live, FED_CAT_LABEL))
    art.append(law_sections(live, FED_CATS, review, "Nothing in this category on the map yet."))
    if failed:
        art.append(law_failed_section(failed, "Withdrawn, revoked or failed"))
    art.append(law_checked_foot(ents))
    art.append("</article>")
    desc = describe(["Federal laws, rules, guidance and executive orders on artificial intelligence in health care, with what each changes for physicians "
                     "and a link to its text.", summary])
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Federal: AI health law and policy", "url": absurl(FED_URL), "description": desc,
          "dateModified": TODAY_ISO, "about": {"@type": "Country", "name": "United States"}, "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}}
    body = '<section class="panel">' + "".join(art) + subscribe_box() + "</section>"
    page(FED_URL, "Federal AI health law and policy", desc, body, active="/law-map/", jsonld=[ld, crumb_ld], head_extra=law_css(body))


def reviewed_state_page(code, review, fed_line):
    """The page for a state that was reviewed with nothing in scope found: the arguments for page()."""
    name = STATE_NAME[code]
    path = law_state_url(code)
    summary = "No state law, rule, insurance bulletin or bill in the map's scope was found in the review of %s." % fmt(review["reviewed"])
    crumb_ld, crumb_html = breadcrumbs([(NAME, "/"), ("Law map", "/law-map/"), (name, None)])
    art = [crumb_html, '<article class="post lawstate"><div class="post-date">AI health law map</div>',
           '<h1 class="headline">%s: AI health laws</h1>' % esc(name), '<p class="standfirst">%s</p>' % esc(summary)]
    note = (review.get("note") or "").strip()
    if note:
        art.append('<p class="lm-note law-intro">%s</p>' % rich(note))
    art.append('<p class="lm-note law-intro">The map looks for laws, rules, insurance-department and licensing-board policies, and bills that have passed '
               'a committee, in five categories: %s.</p>' % esc(join_and([cat_lower(l) for k, l, _ in LAW_CATS])))
    art.append(fed_line)
    art.append(LAW_FOOT % "")
    art.append("</article>")
    desc = describe(["%s: %s" % (name, summary), note])
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "%s: AI health laws" % name, "url": absurl(path), "description": desc,
          "dateModified": TODAY_ISO, "about": {"@type": "State", "name": name}, "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}}
    body = '<section class="panel">' + "".join(art) + subscribe_box() + "</section>"
    return dict(path=path, title="%s AI health laws" % name, desc=desc, body=body, active="/law-map/", jsonld=[ld, crumb_ld], head_extra=law_css(body))


def build_law_map():
    global LLMS_EXTRA
    by_state = {}
    for e in STATE_LAWS:
        by_state.setdefault(e["state"], []).append(e)
    states = sorted(by_state, key=lambda c: STATE_NAME[c])
    reviewed = {c: r for c, r in LAW_REVIEWS.items() if c in STATE_NAME}
    EXP_COUNTS["laws"], EXP_COUNTS["states"] = len(STATE_LAWS), len(states)
    # the federal page comes first, so that nothing links to it unless it was built
    fed, fed_row = [], None
    if FED_LAWS:
        try:
            build_federal_page(FED_LAWS, LAW_REVIEWS.get("US"))
            fed, fed_row = FED_LAWS, (FED_URL, TODAY_ISO, "weekly", "0.7")
        except Exception as ex:  # the federal page must not take the state map down with it
            import traceback
            traceback.print_exc()
            print("warning: the federal law page was not built: %s" % ex, file=sys.stderr)
    EXP_COUNTS["federal"] = len(fed)
    fed_live = [e for e in fed if e.get("status") != "failed"]
    shown = [e for e in LAWS if not is_fed(e) or fed]  # every entry the /law-map/ lists may name, in the page's JSON order
    fed_line = FED_LINE if fed else ""
    # reviewed states with no entries: their pages are made ready first, so the map links only to pages that exist
    none_pages = {}
    for code in sorted((c for c in reviewed if c not in by_state), key=lambda c: STATE_NAME[c]):
        try:
            none_pages[code] = reviewed_state_page(code, reviewed[code], fed_line)
        except Exception as ex:
            print("warning: the law map page for %s was not built: %s" % (STATE_NAME[code], ex), file=sys.stderr)
    none_found = sorted(none_pages, key=lambda c: STATE_NAME[c])
    EXP_COUNTS["reviewed_none"] = len(none_found)

    def live_count(entries, cat):
        return sum(1 for e in entries if e.get("status") in ("enacted", "effective") and (cat == "all" or cat in law_cats(e)))

    def lv(n):
        return 3 if n >= 4 else 2 if n >= 2 else 1 if n >= 1 else 0

    tiles = []
    for code, (col, row) in sorted(TILES.items(), key=lambda kv: (kv[1][1], kv[1][0])):
        pos = "grid-column:%d;grid-row:%d" % (col, row)
        if code in by_state:
            ents = by_state[code]
            counts = [("all", live_count(ents, "all"))] + [(k, live_count(ents, k)) for k, _, _ in LAW_CATS]
            n = counts[0][1]
            tiles.append('<a class="tile lv-%d" href="%s" style="%s" %s title="%s" aria-label="%s: %d %s enacted or in force"><span>%s</span></a>'
                         % (lv(n), law_state_url(code), pos, " ".join('data-%s="%d"' % kv for kv in counts), esc(STATE_NAME[code]),
                            esc(STATE_NAME[code]), n, "law or rule" if n == 1 else "laws and rules", code))
        elif code in none_pages:
            label = "%s: reviewed, none found" % STATE_NAME[code]
            tiles.append('<a class="tile lv-0" href="%s" style="%s" %s title="%s" aria-label="%s"><span>%s</span></a>'
                         % (law_state_url(code), pos, " ".join('data-%s="0"' % k for k in ["all"] + [k for k, _, _ in LAW_CATS]), esc(label), esc(label), code))
        else:
            tiles.append('<span class="tile nr" style="%s" title="%s: not yet reviewed" aria-hidden="true"><span>%s</span></span>' % (pos, esc(STATE_NAME[code]), code))
    names = [STATE_NAME[c] for c in states]
    covered = set(by_state) | set(reviewed)
    if len(covered) == len(STATE_NAME):
        latest = max([r["reviewed"] for r in reviewed.values()] or [""])
        reach = ("Every state has been reviewed; the most recent review was %s." % fmt(latest)) if latest else "Every state has been reviewed."
    elif reviewed:
        reach = ("It covers %d states so far; others are added as they are reviewed." % len(covered)) if len(covered) > 1 else \
                ("The map starts with %s; other states are added as they are reviewed." % STATE_NAME[next(iter(covered))])
    elif len(states) == 1:
        reach = "The map starts with %s; other states are added as they are reviewed." % names[0]
    elif states:
        reach = "It covers %d states so far (%s); others are added as they are reviewed." % (len(states), join_and(names))
    else:
        reach = ""
    what = "State and federal laws, rules and bills" if fed else "State laws, rules and bills"
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">AI health law map</h1><span class="sub">%s laws on AI in health care</span></div>' % ("state and federal" if fed else "state"),
            '<p class="lead">%s on artificial intelligence in health care, each with what it changes in practice for a physician '
            'and a link to its own text.%s</p>' % (what, (" " + esc(reach)) if reach else "")]
    body.append('<div class="lawmap-filter" role="group" aria-label="Shade the map by category" hidden>'
                '<button type="button" class="chip" data-cat="all" aria-pressed="true">All categories</button>'
                + "".join('<button type="button" class="chip" data-cat="%s" aria-pressed="false">%s</button>' % (k, esc(l)) for k, l, _ in LAW_CATS) + "</div>")
    body.append('<div class="tilemap">%s</div>' % "".join(tiles))
    unreviewed = any(c not in by_state and c not in none_pages for c in STATE_NAME)
    body.append('<div class="tile-legend">%s<span><i class="tile-key lv-0"></i>None in force</span>'
                '<span><i class="tile-key lv-1"></i>1</span><span><i class="tile-key lv-2"></i>2 to 3</span><span><i class="tile-key lv-3"></i>4 or more</span></div>'
                '<p class="tile-cap" id="lawmap-cap">Shaded by the number of laws and rules enacted or in force.</p>'
                % ('<span><i class="tile-key nr"></i>Not yet reviewed</span>' if unreviewed else ""))
    if fed:
        on = join_and([cat_lower(l) for k, l, _ in FED_CATS if any(e.get("category") == k for e in fed_live)])
        body.append('<p class="lm-fed"><a href="%s">Federal law and policy</a>: %d %s%s.</p>'
                    % (FED_URL, len(fed_live), "entry" if len(fed_live) == 1 else "entries", (" on " + esc(on)) if on else ""))
    if states:
        body.append('<p class="tile-states">States on the map: %s.</p>' % ", ".join(
            '<a href="%s">%s</a> (%d)' % (law_state_url(c), esc(STATE_NAME[c]), len([e for e in by_state[c] if e.get("status") != "failed"])) for c in states))
    if none_found:
        body.append('<p class="tile-states">Reviewed, none found: %s.</p>' % ", ".join(
            '<a href="%s">%s</a>' % (law_state_url(c), esc(STATE_NAME[c])) for c in none_found))
    # dates ahead
    ahead = sorted([e for e in shown if e.get("status") in ("enacted", "passed") and _iso(e.get("effective")) and e["effective"] > TODAY_ISO],
                   key=lambda e: (e["effective"], e["state"], e.get("name") or ""))
    soon = [e for e in ahead if (datetime.date.fromisoformat(e["effective"]) - TODAY_D).days <= 90]
    if soon:
        body.append('<h2 class="lm-h">Taking effect in the next 90 days</h2><ul class="archive">%s</ul>' % "".join(law_line(e, fmt(e["effective"])) for e in soon))
    elif ahead:
        body.append('<h2 class="lm-h">Taking effect next</h2><p class="lm-note">Nothing on the map takes effect in the next 90 days. The next dates:</p>'
                    '<ul class="archive">%s</ul>' % "".join(law_line(e, fmt(e["effective"])) for e in ahead[:8]))
    # new or changed: a day with more than 8 entries added (and not changed since) shows as one line
    recent = []
    for e in shown:
        d = e.get("changed") if _iso(e.get("changed")) else (e.get("added") if _iso(e.get("added")) else "")
        if d and 0 <= (TODAY_D - datetime.date.fromisoformat(d)).days <= 30:
            recent.append((d, e))
    recent.sort(key=lambda x: (x[0], x[1]["state"]), reverse=True)
    if recent:
        added_on = {}
        for d, e in recent:
            if not law_is_update(e):
                added_on.setdefault(d, []).append(e)
        bulk = {d: es for d, es in added_on.items() if len(es) > 8}
        rows, lines = [], 0
        for day in sorted(set(d for d, _ in recent), reverse=True):
            if day in bulk:
                rows.append(law_bulk_line(day, bulk[day]))
            for d, e in recent:
                if d != day or (day in bulk and not law_is_update(e)) or lines >= 12:
                    continue
                rows.append(law_line(e, ("Updated " if law_is_update(e) else "Added ") + fmt(d)))
                lines += 1
        body.append('<h2 class="lm-h">New or changed in the last 30 days</h2><ul class="archive">%s</ul>' % "".join(rows))
    all_reviewed = not unreviewed  # every state has entries or a page saying none were found
    body.append('<div class="method"><h2>How the map works</h2>'
                '<p>The map records state statutes, agency and attorney general rules, and licensing-board and insurance-department policies on AI in health care, '
                'in five categories: ' + esc(join_and([cat_lower(l) for k, l, _ in LAW_CATS])) + '. '
                'A bill goes on the map once it has passed at least one committee, and a failed bill keeps its entry, marked failed.'
                + (' A state with no entries was reviewed and nothing in scope was found; its page says so.' if all_reviewed else '')
                + ('' if fed else ' Federal rules are covered in the <a href="/posts/">daily posts</a> and on the <a href="/watch/">watch list</a>.') + '</p>'
                + (('<p>The <a href="%s">federal section</a> records statutes, final and proposed rules, agency guidance, executive orders and CMS programs, '
                    'in %s categories: %s, and lists a bill in Congress once it has passed a committee.</p>'
                    % (FED_URL, NUM_WORD.get(len(FED_CATS), str(len(FED_CATS))), esc(join_and([cat_lower(l) for k, l, _ in FED_CATS])))) if fed else '')
                + '<p>Statuses: <strong>introduced</strong> (a bill filed, or a rule proposed), <strong>passed</strong> (passed the legislature, awaiting the governor), '
                '<strong>enacted</strong> (signed, or a rule adopted, with its main duties not yet in force), <strong>in force</strong> (its main duties apply now), '
                '<strong>failed</strong> (died, vetoed or withdrawn) and <strong>blocked</strong> (enjoined, stayed, or delayed with no new date).'
                + (' Federal items use the same statuses, shown as proposed or draft, final, in force or in effect, and withdrawn or revoked.' if fed else '') + '</p>'
                '<p>Every entry links to its primary text first: the enacted bill or its page on the legislature\'s site, the rule, or the agency\'s page. A law firm\'s '
                'summary may follow, labeled secondary, but never stands alone. The physician read says what changes in practice and from when; it states duties '
                'and dates, not advice. The map is updated from the site\'s daily research, each entry shows the date its sources were last checked, and a mistake is '
                'corrected in place with a note.</p>'
                '<p>This is general information, not legal advice. The whole map is available as data at <a href="/law-map/laws.json">/law-map/laws.json</a>.</p></div>')
    ld = {"@context": "https://schema.org", "@type": "Dataset", "name": "AI health law map", "url": absurl("/law-map/"),
          "description": "%s on artificial intelligence in health care, each with what it changes in practice for a physician and a link to its text." % what,
          "dateModified": TODAY_ISO, "creator": PUBLISHER, "isAccessibleForFree": True, "inLanguage": "en-US",
          "spatialCoverage": {"@type": "Place", "name": "United States"},
          "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": absurl("/law-map/laws.json")}}
    desc = ("State and federal laws on AI in health care, with what each changes for physicians and a link to its text: payer AI, disclosure, chatbots, "
            "mental health, privacy and FDA." if fed else
            "State laws on AI in health care, with what each changes for physicians and a link to its text: payer AI, patient disclosure, chatbots, mental health and privacy.")
    main_body = '<section class="panel">' + "".join(body) + subscribe_box() + "</section>"
    page("/law-map/", "AI health law map", desc, main_body + LAWMAP_SCRIPT, active="/law-map/", jsonld=ld, head_extra=law_css(main_body))
    urls.append(("/law-map/", TODAY_ISO, "weekly", "0.8"))
    if fed_row:
        urls.append(fed_row)
    data_out = {"name": "AI health law map", "url": absurl("/law-map/"), "updated": TODAY_ISO, "categories": {k: l for k, l, _ in LAW_CATS}}
    if fed:
        data_out["federal_categories"] = {k: l for k, l, _ in FED_CATS}
    data_out["statuses"] = LAW_STATUS
    data_out["laws"] = sorted(shown, key=lambda e: (e["state"], e["category"], e.get("id") or ""))
    if LAW_REVIEWS:
        data_out["reviews"] = [{"state": c, "reviewed": LAW_REVIEWS[c]["reviewed"]} for c in sorted(LAW_REVIEWS)]
    write("/law-map/laws.json", json.dumps(data_out, ensure_ascii=False, indent=1) + "\n")
    # one page per state with entries
    for code in states:
        ents = law_sorted(by_state[code])
        name = STATE_NAME[code]
        path = law_state_url(code)
        review = reviewed.get(code)
        live = [e for e in ents if e.get("status") != "failed"]
        failed = [e for e in ents if e.get("status") == "failed"]
        summary = state_summary(ents)
        crumb_ld, crumb_html = breadcrumbs([(NAME, "/"), ("Law map", "/law-map/"), (name, None)])
        art = [crumb_html, '<article class="post lawstate"><div class="post-date">AI health law map</div>',
               '<h1 class="headline">%s: AI health laws</h1>' % esc(name), '<p class="standfirst">%s</p>' % esc(summary)]
        note = ((review or {}).get("note") or "").strip()
        if note:
            art.append('<p class="lm-note law-intro">%s</p>' % rich(note))
        art.append(law_dates_ahead(live, LAW_CAT_LABEL))
        art.append(law_sections(live, LAW_CATS, review, ("Nothing in this category was found in the review of %s." % fmt(review["reviewed"]))
                                if review else "Nothing in this category on the map yet."))
        if failed:
            art.append(law_failed_section(failed, "Failed or withdrawn"))
        art.append(fed_line)
        art.append(law_checked_foot(ents))
        art.append("</article>")
        desc = describe(["%s's laws and rules on artificial intelligence in health care, with what each changes for physicians and a link to its text. %s" % (name, summary)])
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "%s: AI health laws" % name, "url": absurl(path), "description": desc,
              "dateModified": TODAY_ISO, "about": {"@type": "State", "name": name}, "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}}
        state_body = '<section class="panel">' + "".join(art) + subscribe_box() + "</section>"
        page(path, "%s AI health laws" % name, desc, state_body, active="/law-map/", jsonld=[ld, crumb_ld], head_extra=law_css(state_body))
        urls.append((path, TODAY_ISO, "weekly", "0.7"))
    # one page per reviewed state with nothing in scope found
    for code in none_found:
        page(**none_pages[code])
        urls.append((none_pages[code]["path"], TODAY_ISO, "weekly", "0.7"))
    if fed:
        LLMS_EXTRA += "- [AI health law map](%s): state and federal laws on AI in health care, each with a physician's read; data at %s\n" % (absurl("/law-map/"), absurl("/law-map/laws.json"))
        LLMS_EXTRA += ("- [Federal AI health law and policy](%s): federal statutes, rules, guidance and executive orders on AI in health care, each with a physician's read\n"
                       % absurl(FED_URL))
    else:
        LLMS_EXTRA += "- [AI health law map](%s): state laws on AI in health care, each with a physician's read; data at %s\n" % (absurl("/law-map/"), absurl("/law-map/laws.json"))


def money(v):
    if isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        return "${:,.0f}".format(v)
    return str(v or "")


def short_url(u):
    u = re.sub(r"^https?://(www\.)?", "", u or "")
    return u.rstrip("/")


RHTP_AI = {"yes": "Yes", "no": "No", "not found": "Not found in the plan's text"}
OPP_STATUS = {"upcoming": "Upcoming", "open": "Open", "closed": "Closed", "awarded": "Awarded"}


def build_rhtp():
    global LLMS_EXTRA
    rows = sorted(RHTP, key=lambda r: STATE_NAME[r["state"]])
    EXP_COUNTS["rhtp"] = len(rows)
    names = [STATE_NAME[r["state"]] for r in rows]
    reach = ("The tracker starts with %s; other states are added as they are reviewed." % names[0]) if len(rows) == 1 else \
            ("It covers %d states so far; others are added as they are reviewed." % len(rows))
    special = next((sl for sl, sp in special_pages if sl == "rural-health-transformation-program"), None)
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Rural Health Transformation Program tracker</h1><span class="sub">state by state</span></div>',
            '<p class="lead">The Rural Health Transformation Program sends $10 billion a year to the 50 states for fiscal years 2026 through 2030, under '
            '<a href="https://www.cms.gov/files/document/chapter-4-protecting-rural-health-hospitals-providers.pdf" target="_blank" rel="noopener">the budget law signed July 4, 2025</a>. '
            'Hospitals, clinics and other providers get the money through their state\'s funding rounds. This tracker follows each state\'s first-year award, where its plan '
            'names AI or other technology, its funding rounds and deadlines, and its awards, each linked to its source. %s</p>' % esc(reach)]
    extra = []
    if special:
        extra.append('How a rural hospital gets some of the money: <a href="%s">the special topic</a>.' % special_url(special))
    extra.append('For states not yet on the tracker, the Rural Health Information Hub <a href="https://www.ruralhealthinfo.org/resources/lists/rhtp" target="_blank" rel="noopener">lists every state\'s program page and lead agency</a>.')
    body.append('<p class="lm-note">%s</p>' % " ".join(extra))
    # open and upcoming rounds
    opps = []
    for r in rows:
        for o in r.get("opportunities") or []:
            if isinstance(o, dict) and (o.get("status") or "").lower() in ("open", "upcoming"):
                opps.append((o.get("deadline") if _iso(o.get("deadline")) else "9999", r, o))
    opps.sort(key=lambda x: x[0])
    body.append('<h2 class="lm-h">Open and upcoming funding rounds</h2>')
    if opps:
        body.append('<ul class="archive">')
        for dl, r, o in opps:
            title = ext_link(o.get("title") or "Funding round", o["url"]) if o.get("url") else esc(o.get("title") or "Funding round")
            bits = [STATE_NAME[r["state"]], OPP_STATUS.get((o.get("status") or "").lower(), "")]
            if o.get("amount"):
                bits.append(str(o["amount"]))
            if o.get("eligible"):
                bits.append("for " + str(o["eligible"]))
            body.append('<li><span class="when">%s</span><div><span class="rt">%s</span><div class="d">%s</div></div></li>'
                        % (esc(("Due " + fmt(dl)) if dl != "9999" else "Date not set"), title, esc(" · ".join(b for b in bits if b))))
        body.append("</ul>")
    else:
        body.append('<p class="lm-note">No open or upcoming state funding rounds are on the tracker as of %s.</p>' % esc(fmt(TODAY_ISO)))
    # the table
    body.append('<h2 class="lm-h">States on the tracker</h2><div class="tablewrap"><table><thead><tr><th>State</th><th>First-year award</th><th>AI named in the plan</th><th>Latest</th><th>Checked</th></tr></thead><tbody>')
    for r in rows:
        aw = [a for a in (r.get("awards") or []) if isinstance(a, dict)]
        aw.sort(key=lambda a: a.get("date") or "", reverse=True)
        latest = ""
        if aw:
            a = aw[0]
            latest = "%s: %s%s" % (fmt(a.get("date")), a.get("amount") or "awards", (" to " + str(a["recipients"])) if a.get("recipients") else "")
        body.append('<tr><td><a href="#%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                    % (r["state"].lower(), esc(STATE_NAME[r["state"]]), esc(money(r.get("award_fy2026"))), esc(RHTP_AI.get((r.get("ai_named") or "").lower(), r.get("ai_named") or "")),
                       esc(latest), esc(fmt(r.get("checked")) if _iso(r.get("checked")) else "")))
    body.append("</tbody></table></div>")
    # one card per state
    for r in rows:
        name = STATE_NAME[r["state"]]
        f = []
        if r.get("award_fy2026") not in (None, ""):
            f.append(("First-year award", esc(money(r["award_fy2026"])) + ((" (%s)" % ext_link("CMS", r["award_url"])) if r.get("award_url") else "")))
        if r.get("lead_agency"):
            f.append(("Lead agency", rich(r["lead_agency"])))
        if r.get("program_url"):
            f.append(("Program page", ext_link(short_url(r["program_url"]), r["program_url"])))
        if r.get("contact_url"):
            f.append(("Contact", ext_link("The program office's contact details", r["contact_url"])))
        if r.get("technology"):
            f.append(("Where the plan names technology", rich(r["technology"])))
        if r.get("ai_named"):
            f.append(("AI named in the plan", esc(RHTP_AI.get(r["ai_named"].lower(), r["ai_named"]))))
        ops = [o for o in (r.get("opportunities") or []) if isinstance(o, dict)]
        if ops:
            li = []
            for o in sorted(ops, key=lambda o: o.get("deadline") or "", reverse=True):
                when = []
                if _iso(o.get("opens")):
                    when.append("opened " + fmt(o["opens"]))
                if _iso(o.get("deadline")):
                    when.append("deadline " + fmt(o["deadline"]))
                t_ = ext_link(o.get("title") or "Funding round", o["url"]) if o.get("url") else esc(o.get("title") or "Funding round")
                parts = [x for x in (esc(o.get("amount") or ""), esc(", ".join(when)), esc(("eligible: " + o["eligible"]) if o.get("eligible") else "")) if x]
                li.append('<li><span class="lstat st-%s">%s</span> %s%s</li>' % (esc(slugify(o.get("status") or "")), esc(OPP_STATUS.get((o.get("status") or "").lower(), o.get("status") or "")),
                                                                                 t_, ("; " + "; ".join(parts)) if parts else ""))
            f.append(("Funding rounds", "<ul>%s</ul>" % "".join(li)))
        aws = [a for a in (r.get("awards") or []) if isinstance(a, dict)]
        if aws:
            li = []
            for a in sorted(aws, key=lambda a: a.get("date") or "", reverse=True):
                head = " ".join(x for x in (fmt(a.get("date")) + ":" if a.get("date") else "", a.get("amount") or "", ("to " + a["recipients"]) if a.get("recipients") else "") if x)
                li.append("<li>%s%s%s</li>" % (esc(head), (". " + rich(a["summary"])) if a.get("summary") else "", (" " + ext_link("Announcement", a["url"])) if a.get("url") else ""))
            f.append(("Awards", "<ul>%s</ul>" % "".join(li)))
        if r.get("notes"):
            f.append(("Next", rich(r["notes"])))
        card = ['<section class="rhtp-state" id="%s"><h2>%s</h2><dl class="facts">%s</dl>' % (r["state"].lower(), esc(name), "".join("<dt>%s</dt><dd>%s</dd>" % (esc(k), v) for k, v in f))]
        card.append(sources_line("law-src", r.get("sources") if isinstance(r.get("sources"), list) else []))
        if _iso(r.get("checked")):
            card.append('<div class="law-checked">Checked against its sources <time datetime="%s">%s</time></div>' % (esc(r["checked"]), esc(fmt(r["checked"]))))
        card.append("</section>")
        body.append("".join(card))
    body.append('<p class="law-foot">General information, not legal or financial advice. The tracker is updated from the site\'s daily research, and each state shows the date its sources were last checked.</p>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Rural Health Transformation Program tracker", "url": absurl("/rhtp/"),
          "description": "The Rural Health Transformation Program state by state: awards, where plans name AI and technology, funding rounds, deadlines and awards.",
          "dateModified": TODAY_ISO, "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}}
    page("/rhtp/", "Rural Health Transformation Program tracker", "The Rural Health Transformation Program state by state: first-year awards, where plans name AI and technology, funding rounds, deadlines and awards, each linked to its source.",
         '<section class="panel">' + "".join(body) + subscribe_box() + "</section>", active="/rhtp/", jsonld=ld)
    urls.append(("/rhtp/", TODAY_ISO, "weekly", "0.7"))
    LLMS_EXTRA += "- [Rural Health Transformation Program tracker](%s): the federal program state by state, with awards, funding rounds and deadlines\n" % absurl("/rhtp/")


def cap_first(s):
    s = (s or "").strip()
    return s[:1].upper() + s[1:]


def build_explainers():
    global LLMS_EXTRA
    items = EXPLAINERS
    EXP_COUNTS["explainers"] = len(items)
    for i, x in enumerate(items):
        slug = x["slug"]
        path = explainer_url(slug)
        title = x["title"]
        rev = x.get("reviewed") if _iso(x.get("reviewed")) else (x.get("published") if _iso(x.get("published")) else TODAY_ISO)
        art = ['<article class="post explainer"><div class="post-date">Explainer · Reviewed <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(rev), esc(fmt(rev)), esc(title))]
        art.append(share_html(path, title))
        art.append(figure_html(EXPLAINER_IMG, slug, "letter-art"))
        if x.get("short"):
            art.append('<div class="short-answer"><h2>Short answer</h2><p>%s</p></div>' % rich(x["short"]))
        art.append('<div class="special-body explainer-body">')
        for b in x.get("blocks") or []:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "h":
                art.append("<h2>%s</h2>" % esc(b.get("text", "")))
            elif t == "list":
                tag = "ol" if b.get("ordered", True) else "ul"
                art.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % rich(it) for it in (b.get("items") or []) if it), tag))
            else:
                art.append("<p>%s</p>" % rich(b.get("text", "")))
        art.append("</div>")
        if x.get("changes"):
            art.append('<div class="changes"><h2>What would change this answer</h2><p>%s</p></div>' % rich(cap_first(x["changes"])))
        art.append('<p class="explainer-foot">General information, not legal or medical advice. Every fact links to its source, and the page shows the date it was last reviewed.</p>')
        art.append("</article>")
        older = (items[i + 1]["title"], explainer_url(items[i + 1]["slug"])) if i + 1 < len(items) else None
        newer = (items[i - 1]["title"], explainer_url(items[i - 1]["slug"])) if i > 0 else None
        desc = describe([x.get("short") or title])
        og_i, og_alt = og_for(EXPLAINER_IMG, slug)
        entry_page("Article", path, [(NAME, "/"), ("Explainers", "/explainers/"), (title, None)], title, desc, rev, "".join(art), older, newer,
                   image=og_i, image_alt=og_alt, unsigned=True)
        urls.append((path, rev, "monthly", "0.8"))
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Explainers</h1><span class="sub">plain answers, with the sources</span></div>',
            '<p class="lead">Plain answers to questions physicians and practice leaders ask about AI in medicine. Every fact links to its source, each page shows the date it was '
            'last reviewed, and each ends with what would change the answer.</p><ul class="letter-list">']
    for k, x in enumerate(items):
        rev = x.get("reviewed") if _iso(x.get("reviewed")) else ""
        thumb = list_thumb(EXPLAINER_IMG, x["slug"], explainer_url(x["slug"]), k)
        body.append('<li%s>%s<div class="txt"><span class="when">%s</span><a class="t" href="%s">%s</a>%s</div></li>'
                    % ("" if thumb else ' class="no-thumb"', thumb, esc(("Reviewed " + fmt(rev)) if rev else "Explainer"), explainer_url(x["slug"]), esc(x["title"]),
                       ('<p class="d">%s</p>' % esc(describe([x["short"]], 230))) if x.get("short") else ""))
    body.append("</ul>")
    page("/explainers/", "Explainers", "Plain answers to common questions about AI in medicine, from HIPAA and chatbots to AI scribe liability and Medicare payment, each linked to its sources and dated.",
         '<section class="panel">' + "".join(body) + subscribe_box() + "</section>", active="/explainers/",
         jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "Explainers", "url": absurl("/explainers/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
    urls.append(("/explainers/", TODAY_ISO, "weekly", "0.8"))
    LLMS_EXTRA += "- [Explainers](%s): plain answers to common questions about AI in medicine, each dated when reviewed\n" % absurl("/explainers/")


CITE_RE = re.compile(r"\s*\((?:\[[^\]]+\]\(https?://[^\s)]+\)(?:;\s*)?)+\)")


def spoken(text):
    """Plain text for reading aloud: the parenthetical source links are dropped, other links keep their words."""
    return plain(CITE_RE.sub("", "" if text is None else str(text)))


def patient_record(x):
    lines = []
    for b in x.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        line = spoken(((b.get("lead") or "") + " " + (b.get("text") or "")).strip() if b.get("type") == "ask" else b.get("text"))
        if line:
            lines.append(line)
    return {"weekOf": x["weekOf"], "date": x.get("date") or x["weekOf"], "headline": plain(x.get("headline") or ""), "dek": plain(x.get("dek") or ""),
            "url": absurl(patient_url(x["weekOf"])), "intro": spoken(x.get("intro")), "body": lines,
            "question_heading": "One question for your next appointment", "question": spoken(x.get("question")), "closing": spoken(x.get("closing"))}


PATIENT_TAIL = ('<div class="subscribe-box"><p>A weekly letter for patients and families on how AI is showing up in health care, in plain language.</p>'
                '<div class="subscribe-actions"><a class="btn" href="/patients/">All letters for patients</a></div></div>')


def build_patients():
    global LLMS_EXTRA
    items = PATIENTS
    EXP_COUNTS["patients"] = len(items)
    for i, x in enumerate(items):
        path = patient_url(x["weekOf"])
        wk = "Week of " + fmt(x["weekOf"])
        headline = x["headline"]
        art = ['<article class="post patient"><div class="post-date">For patients · <time datetime="%s">%s</time></div><h1 class="headline">%s</h1>' % (esc(x["weekOf"]), esc(wk), esc(headline))]
        if x.get("dek"):
            art.append('<p class="standfirst">%s</p>' % rich(x["dek"]))
        art.append(share_html(path, headline))
        art.append('<p class="patient-note">General information for patients and families, not medical advice. Each letter is reviewed by a physician before it is published.</p>')
        art.append('<div class="special-body patient-body">')
        if x.get("intro"):
            art.append('<p class="patient-intro">%s</p>' % rich(x["intro"]))
        for b in x.get("blocks") or []:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "h":
                art.append("<h2>%s</h2>" % esc(b.get("text", "")))
            elif t == "ask":
                art.append('<p class="ask"><strong>%s</strong> %s</p>' % (esc(b.get("lead", "")), rich(b.get("text", ""))))
            else:
                art.append("<p>%s</p>" % rich(b.get("text", "")))
        art.append("</div>")
        if x.get("question"):
            art.append('<div class="one-question"><h2>One question for your next appointment</h2><p>%s</p></div>' % rich(x["question"]))
        if x.get("closing"):
            art.append('<p class="patient-closing">%s</p>' % rich(x["closing"]))
        art.append("</article>")
        older = (items[i + 1]["headline"], patient_url(items[i + 1]["weekOf"])) if i + 1 < len(items) else None
        newer = (items[i - 1]["headline"], patient_url(items[i - 1]["weekOf"])) if i > 0 else None
        rec = patient_record(x)
        write(path + "letter.json", json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        if i == 0:
            write("/patients/latest.json", json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        desc = describe([x.get("dek") or x.get("intro") or headline])
        entry_page("Article", path, [(NAME, "/"), ("For patients", "/patients/"), (wk, None)], headline, desc, x.get("date") or x["weekOf"], "".join(art),
                   older, newer, unsigned=True, tail=PATIENT_TAIL)
        urls.append((path, x.get("date") or x["weekOf"], "monthly", "0.7"))
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">For patients</h1><span class="sub">a weekly letter for patients and families</span></div>',
            '<p class="lead">A weekly letter in plain language on how artificial intelligence is showing up in health care: in the exam room, in insurance decisions, '
            'and in the apps and chatbots people use at home. Each letter is reviewed by a physician before it is published. It is general information, not medical '
            'advice: talk with your own doctor about your care.</p><ul class="letter-list">']
    for x in items:
        body.append('<li class="no-thumb"><div class="txt"><span class="when">%s</span><a class="t" href="%s">%s</a>%s</div></li>'
                    % (esc("Week of " + fmt(x["weekOf"])), patient_url(x["weekOf"]), esc(x["headline"]), ('<p class="d">%s</p>' % esc(plain(x["dek"]))) if x.get("dek") else ""))
    body.append("</ul>")
    page("/patients/", "For patients", "A weekly letter for patients and families on how artificial intelligence is showing up in health care, in plain language, reviewed by a physician.",
         '<section class="panel">' + "".join(body) + "</section>", active="/patients/",
         jsonld={"@context": "https://schema.org", "@type": "CollectionPage", "name": "For patients", "url": absurl("/patients/"), "isPartOf": {"@type": "WebSite", "name": NAME, "url": SITE}})
    urls.append(("/patients/", TODAY_ISO, "weekly", "0.7"))
    LLMS_EXTRA += "- [For patients](%s): a weekly letter for patients and families, in plain language\n" % absurl("/patients/")


for _label, _fn, _have in (("patient letters", build_patients, PATIENTS), ("law map", build_law_map, LAWS), ("program tracker", build_rhtp, RHTP), ("explainers", build_explainers, EXPLAINERS)):
    if not _have:
        continue
    try:
        _fn()
    except Exception as _ex:  # a mistake in one section's data must not stop the morning publish
        import traceback
        traceback.print_exc()
        print("warning: the %s section was not built: %s" % (_label, _ex), file=sys.stderr)


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
        '<p class="lead">These are the signals we check first every morning. A status changes only when something real happens, and the note says what.</p>',
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
_m = re.search(r'<p class="lede">.*?</p>', land, re.S) or re.search(r'</h1>', land)  # 2.16
if _m:
    land = land[:_m.end()] + share_html("/where-things-stand/", land_title) + land[_m.end():]
ld_land = article_ld("Article", absurl("/where-things-stand/"), land_title, land_desc, LAST_UPDATED)
page("/where-things-stand/", land_title, land_desc, '<section class="panel doc">' + land + subscribe_box() + "</section>", active="/where-things-stand/", kind="article", jsonld=ld_land)
urls.append(("/where-things-stand/", LAST_UPDATED, "monthly", "0.8"))

# ------------------------------------------------------------------ about
# ------------------------------------------------------------------ podcast
if POD:
    ld_pod = {"@context": "https://schema.org", "@type": "PodcastSeries", "name": POD["name"], "url": absurl("/podcast/"), "webFeed": POD["rss"],
              "description": POD_BLURB, "inLanguage": "en-US", "author": ORG_AUTHOR, "publisher": PUBLISHER,
              "sameAs": [u for u in (POD.get("apple"), POD.get("spotify"), POD.get("youtube")) if u]}
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Podcast</h1><span class="sub">every episode, playable here</span></div>',
            '<p class="lead">%s Play any episode below, or follow the show in Apple Podcasts, Spotify or any app that takes an RSS feed.</p>' % esc(POD_BLURB),
            pod_embed("playlist", int(POD.get("playlist_height") or 390), "Every episode of the %s podcast" % POD["name"]),
            '<h2 class="pod-follow">Follow the show</h2>', pod_apps(),
            '<p class="pod-feed">In any other podcast app, add the feed: <code>%s</code></p>' % esc(POD["rss"]), POD_SCRIPT]
    page("/podcast/", "Podcast", "Every episode of the %s podcast, each morning's post as an audio briefing, playable here or in Apple Podcasts and Spotify." % POD["name"],
         '<section class="panel">' + "".join(body) + "</section>", active="/podcast/", jsonld=ld_pod)
    urls.append(("/podcast/", LAST_UPDATED, "daily", "0.8"))

_founder = {**FOUNDER, **({"image": absurl(photo_path)} if photo_path else {})}
ld_about = {"@context": "https://schema.org", "@type": "AboutPage", "name": "About " + NAME, "url": absurl("/about/"),
            "mainEntity": {"@type": "Organization", "name": NAME, "url": SITE, "logo": PUBLISHER["logo"],
                           **({"parentOrganization": {"@type": "Organization", "name": PUBLISHED_BY, "founder": _founder}} if PUBLISHED_BY != NAME else {"founder": _founder})}}
ABOUT_CONTACT = ('<h3 style="margin-top:22px">Contact</h3><p>Questions, corrections, news tips and press requests reach us through the <a href="/contact/">contact form</a>.</p>'
                 if CONTACT_LIVE else "")
page("/about/", "About", "%s is published by %s. It sorts what matters in artificial intelligence in medicine from the noise, for patients and the people who practice on the front lines." % (NAME, PUBLISHED_BY),
     '<section class="panel"><div class="panel-head"><h1 style="font-size:1.6rem">About</h1></div>' + about_inner + ABOUT_CONTACT + "</section>", active="/about/", jsonld=ld_about)
urls.append(("/about/", LAST_UPDATED, "monthly", "0.5"))

# ------------------------------------------------------------------ contact (2.15)
CONTACT_CSS = """<style>
  .contact-form { display: grid; gap: 16px; margin-top: 18px; max-width: 620px; }
  .contact-form .field { display: grid; gap: 6px; }
  .contact-form label { font-weight: 600; font-size: 0.95rem; color: var(--ink); }
  .contact-form .hint { font-weight: 400; color: var(--muted); font-size: 0.86rem; }
  .contact-form input, .contact-form select, .contact-form textarea { font: inherit; font-size: 1rem; color: var(--ink); background: var(--surface); border: 1px solid var(--rule-2); border-radius: 10px; padding: 10px 12px; width: 100%; box-sizing: border-box; }
  .contact-form textarea { min-height: 180px; resize: vertical; line-height: 1.5; }
  .contact-form input:focus, .contact-form select:focus, .contact-form textarea:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-color: var(--accent); }
  .contact-form .hp { position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden; }
  .contact-form .actions { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
  .contact-form button.btn { border: 0; cursor: pointer; font: inherit; font-weight: 600; }
  .contact-form button.btn[disabled] { opacity: 0.6; cursor: progress; }
  .form-msg { margin: 16px 0 0; padding: 12px 16px; border-radius: 10px; max-width: 620px; }
  .form-msg.err { background: rgba(178, 59, 59, 0.10); color: var(--bad); }
  .form-note { font-size: 0.9rem; color: var(--muted); margin: 14px 0 0; max-width: 620px; }
</style>"""
CONTACT_TOPICS = ["General question", "Correction", "News tip", "Press or speaking", "Podcast", "Something else"]
CONTACT_ERRORS = {"fields": "Please fill in your name, a valid email address and a message.",
                  "check": "The check that you are a person did not go through. Please try again.",
                  "send": "The message could not be sent just now. Please try again in a few minutes."}
CONTACT_SCRIPT = ("<script>(function(){var M=%s;var box=document.getElementById('form-msg');function show(k){if(!M[k])return;box.textContent=M[k];box.hidden=false;}"
                  "try{show(new URLSearchParams(location.search).get('error'));}catch(e){}"
                  "var f=document.getElementById('contact-form');if(!f||!window.fetch||!window.FormData)return;"
                  "f.addEventListener('submit',function(ev){ev.preventDefault();var b=f.querySelector('button[type=submit]');b.disabled=true;box.hidden=true;"
                  "fetch(f.action,{method:'POST',body:new FormData(f),credentials:'same-origin'}).then(function(r){var u=r.url||'';"
                  "if(r.ok&&u.indexOf('/contact/thanks/')!==-1){location.href='/contact/thanks/';return;}"
                  "var m=/[?&]error=([a-z]+)/.exec(u);show(m?m[1]:'send');b.disabled=false;try{if(window.turnstile)window.turnstile.reset();}catch(e){}})"
                  "['catch'](function(){show('send');b.disabled=false;try{if(window.turnstile)window.turnstile.reset();}catch(e){}});});})();</script>"
                  % json.dumps(CONTACT_ERRORS))
if CONTACT:
    body = ['<div class="panel-head"><h1 style="font-size:1.6rem">Contact</h1><span class="sub">write to us</span></div>',
            '<p class="lead">Questions, corrections, news tips and requests from the press all reach us here. We read every message.</p>',
            '<div class="form-msg err" id="form-msg" role="alert" hidden></div>',
            '<form class="contact-form" id="contact-form" method="post" action="%s">' % esc(CONTACT.get("path") or "/api/contact"),
            '<div class="field"><label for="cf-name">Name</label><input id="cf-name" name="name" type="text" autocomplete="name" maxlength="120" required></div>',
            '<div class="field"><label for="cf-email">Email <span class="hint">(only to reply to you)</span></label><input id="cf-email" name="email" type="email" autocomplete="email" maxlength="254" required></div>',
            '<div class="field"><label for="cf-topic">Topic</label><select id="cf-topic" name="topic">%s</select></div>' % "".join('<option>%s</option>' % esc(t) for t in CONTACT_TOPICS),
            '<div class="field"><label for="cf-message">Message</label><textarea id="cf-message" name="message" maxlength="5000" required></textarea></div>',
            '<div class="hp" aria-hidden="true"><label for="cf-website">Leave this field empty</label><input id="cf-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>',
            '<div class="cf-turnstile" data-sitekey="%s" data-theme="auto" data-action="contact"></div>' % esc(CONTACT["turnstile_sitekey"]),
            '<div class="actions"><button class="btn" type="submit">Send message</button></div>',
            '</form>',
            '<p class="form-note">For a correction, tell us the page and what the source says; corrections are made on the page and marked. '
            'We cannot answer questions about your own health or care, so please leave medical details out of your message. '
            'This form is protected by Cloudflare Turnstile.</p>']
    page("/contact/", "Contact", "Write to %s: questions, corrections, news tips and press requests." % NAME, '<section class="panel">' + "".join(body) + "</section>" + CONTACT_SCRIPT,
         head_extra=CONTACT_CSS + '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>',
         noindex=not CONTACT_LIVE)
    page("/contact/thanks/", "Message sent", "Your message to %s is on its way." % NAME,
         '<section class="panel"><div class="panel-head"><h1 style="font-size:1.6rem">Thank you</h1><span class="sub">message sent</span></div>'
         '<p class="lead">Your message is on its way to us. If it needs an answer, we will reply to the email address you gave.</p>'
         '<div class="more-row"><a class="btn ghost small" href="/">Front page</a><a class="btn ghost small" href="/posts/">Daily posts</a><a class="btn ghost small" href="/letters/">Friday letter</a></div></section>',
         noindex=True)
    if CONTACT_LIVE:
        urls.append(("/contact/", LAST_UPDATED, "yearly", "0.3"))

# ------------------------------------------------------------------ feed, sitemap, robots, extras
def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"

feed_items = []
for slug, p in post_pages:
    feed_items.append((p.get("date") or "", 2, p.get("headline") or "Daily post", absurl(post_url(slug)), describe(p.get("intro") or [p.get("headline")], 300), post_body(p), NAME))
for slug, w in letter_pages:
    feed_items.append((w.get("weekOf") or "", 3, w.get("headline") or "The Friday letter", absurl(letter_url(slug)), plain(w.get("dek") or ""), (('<p><img src="%s" alt="%s" width="1200" height="630"></p>' % (esc(LETTER_IMG[slug][0] if LETTER_IMG[slug][0].startswith("https://") else absurl(LETTER_IMG[slug][0])), esc(LETTER_IMG[slug][1]))) if slug in LETTER_IMG else "") + paras(w.get("body")) + ('<div class="section-label">SOURCE MATERIAL</div>' + render_items(w["top"]) if w.get("top") else "") + (paras(w["outlook"]) if w.get("outlook") else ""), NAME))
for slug, sp in special_pages:
    sp_img = (('<p><img src="%s" alt="%s" width="1200" height="630"></p>' % (esc(SPECIAL_IMG[slug][0] if SPECIAL_IMG[slug][0].startswith("https://") else absurl(SPECIAL_IMG[slug][0])), esc(SPECIAL_IMG[slug][1]))) if slug in SPECIAL_IMG else "")
    feed_items.append((sp.get("date") or "", 1, sp.get("title") or "Special topic", absurl(special_url(slug)), plain(sp.get("dek") or ""),
                       sp_img + "".join("<p>%s</p>" % rich((b.get("lead", "") + " " + b.get("text", "")).strip()) for b in sp.get("blocks") or [])
                       + ('<div class="section-label">SOURCE MATERIAL</div>' + render_items(sp["top"]) if sp.get("top") else ""),
                       NAME))
feed_items.sort(key=lambda x: (x[0], x[1]), reverse=True)
rss = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">',
       "<channel>", "<title>%s</title>" % esc(NAME), "<link>%s</link>" % esc(SITE), "<description>%s</description>" % esc(config["description"]),
       "<language>en-us</language>", '<atom:link href="%s" rel="self" type="application/rss+xml"/>' % esc(absurl("/feed.xml")),
       "<lastBuildDate>%s</lastBuildDate>" % rfc822(LAST_UPDATED), "<image><url>%s</url><title>%s</title><link>%s</link></image>" % (esc(absurl("/logo.png")), esc(NAME), esc(SITE))]
for date, _, title, link, desc, content, creator in feed_items[:40]:
    rss.append("<item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s</guid><pubDate>%s</pubDate><dc:creator>%s</dc:creator><description>%s</description><content:encoded>%s</content:encoded></item>"
               % (esc(title), esc(link), esc(link), rfc822(date), esc(creator), esc(desc), cdata(content)))
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
write("/llms.txt", "# %s\n\n> %s\n\nPublished by %s. Daily posts are third-person news wire copy about artificial intelligence in medicine, each item linked to its original source; the Friday letter is an unsigned editorial in the manner of a leader in The Economist, and the special topics are longer pieces on a single question.\n\n## Sections\n\n- [Daily posts](%s): one post every morning, newest first\n- [Friday letter](%s): the weekly essay with recommendations\n- [Special topics](%s): long pieces on one question\n- [Watch list](%s): the signals that would change the picture\n- [Dates](%s): deadlines, effective dates, hearings\n- [Where things stand](%s): the long read\n- [Topics](%s): the daily items grouped by kind\n- [About](%s)\n- [RSS feed](%s)\n"
      % (NAME, config["description"], PUBLISHED_BY, absurl("/posts/"), absurl("/letters/"), absurl("/specials/"), absurl("/watch/"), absurl("/dates/"), absurl("/where-things-stand/"), absurl("/topics/"), absurl("/about/"), absurl("/feed.xml"))
      + ("- [Podcast](%s): each morning's post as an audio briefing; podcast feed %s\n" % (absurl("/podcast/"), POD["rss"]) if POD else "") + LLMS_EXTRA
      + ("- [Contact](%s): questions, corrections, news tips and press requests\n" % absurl("/contact/") if CONTACT_LIVE else ""))

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
HAS_FUNCTIONS = write_episode_function()
try:
    HAS_CF_FUNCTIONS = write_cloudflare_functions()
    write_retired_functions()
except Exception as ex:  # a Cloudflare problem must never stop the Netlify publish
    HAS_CF_FUNCTIONS = False
    print("warning: the Cloudflare functions were not written: %s" % ex, file=sys.stderr)
try:
    HAS_CONTACT_WORKER = write_contact_worker()
except Exception as ex:  # nor may a contact form problem
    HAS_CONTACT_WORKER = False
    print("warning: the contact form Worker was not written: %s" % ex, file=sys.stderr)
with open(os.path.join(ROOT, "netlify.toml"), "w") as f:
    f.write('[build]\n  publish = "public"\n  command = ""\n' + ('\n[functions]\n  directory = "netlify/functions"\n' if HAS_FUNCTIONS else ""))

n_files = sum(len(fs) for _, _, fs in os.walk(OUT))
print("ok: built %d pages (%d posts, %d letters, %d specials, %d patient letters, %d explainers, %d laws in %d states, %d federal entries, "
      "%d states reviewed with none found, %d program rows), %d files in %s; updated %s; analytics %s; contact form %s"
      % (len(urls), len(post_pages), len(letter_pages), len(special_pages), EXP_COUNTS["patients"], EXP_COUNTS["explainers"], EXP_COUNTS["laws"], EXP_COUNTS["states"],
         EXP_COUNTS["federal"], EXP_COUNTS["reviewed_none"], EXP_COUNTS["rhtp"], n_files, OUT, LAST_UPDATED, (config.get("analytics") or {}).get("provider") or "none",
         ("live" if CONTACT_LIVE else "built, not linked") if CONTACT else "off"))
