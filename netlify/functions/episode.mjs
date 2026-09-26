// Podcast episode lookup for physicianintheloop.org. Written by tools/build_public_site.py on every
// site build; edit the generator, not this file.
//
// GET /api/episode/YYYY-MM-DD finds the episode titled for that date in the show's feed and answers
// {"found": true, "id": "...", "embed": "https://share.transistor.fm/e/<id>", ...}, or {"found": false}
// before the episode exists. Daily post pages call it when they load and show the player only when found.
// Answers are cached on Netlify's CDN: a found episode for an hour, a missing one for two minutes, so a
// new episode appears on its post page within a few minutes of publishing.

const FEED = "https://feeds.transistor.fm/physician-in-the-loop";
const TITLE = "Daily Update for {date}";
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function titleFor(date) {
  const [y, m, d] = date.split("-").map(Number);
  return TITLE.replace("{date}", MONTHS[m - 1] + " " + d + ", " + y);
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

export default async (req, context) => {
  const date = (context && context.params && context.params.date) || new URL(req.url).searchParams.get("date") || "";
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
  const want = plain(titleFor(date));
  for (const chunk of xml.split(/<item[\s>]/i).slice(1)) {
    const item = chunk.split(/<\/item>/i)[0];
    const titles = [...item.matchAll(/<(?:itunes:)?title>([\s\S]*?)<\/(?:itunes:)?title>/gi)].map((t) => plain(t[1]));
    if (!titles.includes(want)) continue;
    const link =
      /<link>\s*https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item) ||
      /<enclosure[^>]+https:\/\/media\.transistor\.fm\/([a-z0-9]+)\//i.exec(item) ||
      /https:\/\/share\.transistor\.fm\/s\/([a-z0-9]+)/i.exec(item);
    if (!link) continue;
    const id = link[1];
    return reply(
      { found: true, date, title: titleFor(date), id, share: "https://share.transistor.fm/s/" + id, embed: "https://share.transistor.fm/e/" + id },
      200,
      "public, max-age=600",
      "public, s-maxage=3600, stale-while-revalidate=86400"
    );
  }
  return reply({ found: false, date }, 200, "public, max-age=60", "public, s-maxage=120");
};

export const config = { path: "/api/episode/:date" };
