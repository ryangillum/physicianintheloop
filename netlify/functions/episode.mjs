// Podcast episode lookup for physicianintheloop.org. Written by tools/build_public_site.py on every
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

const FEED = "https://feeds.transistor.fm/physician-in-the-loop";
const TITLES = ["Daily Briefing for {date}", "Daily Update for {date}"];
const LETTER_PREFIX = "Friday Letter";
const SPECIAL_PREFIX = "Special Topic";
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
