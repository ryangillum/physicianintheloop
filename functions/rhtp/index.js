// Retired page on physicianintheloop.org: /rhtp/. Written by tools/build_public_site.py on every site build;
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
