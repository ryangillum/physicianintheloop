# Contact form Worker

Written by tools/build_public_site.py on every site build; edit the generator, not these files.

The form at https://physicianintheloop.org/contact/ posts to physicianintheloop.org/api/contact, which this Worker answers. It checks the Cloudflare Turnstile
token, emails the message through the Email Routing binding SEND_EMAIL to the verified destination address, and sends the
visitor back to /contact/thanks/ (or to /contact/?error=...).

Cloudflare Workers Builds deploys this folder to the Worker "physicianintheloop-contact" when anything in it changes on main
(root directory `contact-worker`, deploy command `npx wrangler deploy`, build watch path `contact-worker/*`).

One secret is set in the Cloudflare dashboard and never kept here: TURNSTILE_SECRET, the contact form widget's secret key
(Workers & Pages, physicianintheloop-contact, Settings, Variables and Secrets). Wrangler keeps it across deploys.
