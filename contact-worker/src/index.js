// Contact form Worker for physicianintheloop.org (route physicianintheloop.org/api/contact). Written by tools/build_public_site.py on every
// site build; edit the generator, not this file. Cloudflare Workers Builds deploys this folder when it changes.
//
// The form at /contact/ posts here. The Worker checks the Cloudflare Turnstile token (secret TURNSTILE_SECRET, set in
// the dashboard and never kept in the repository), emails the message through the Email Routing binding SEND_EMAIL to the
// verified destination address, and sends the visitor back to /contact/thanks/ or to /contact/?error=fields|check|send.
import { EmailMessage } from "cloudflare:email";

const SITE = "https://physicianintheloop.org";
const HOST = "physicianintheloop.org";
const TO = "ryangillum@nomadmedical.org";
const FROM = "contact-form@physicianintheloop.org";
const NAME = "Physician in the Loop";

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
