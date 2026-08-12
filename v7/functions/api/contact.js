/**
 * POST /api/contact
 *
 * Cloudflare Pages Function. Receives the contact form, screens it, and pushes
 * it to Day AI. Runs on the Pages free tier.
 *
 * The rule this is built around: an enquiry must never be lost. If Day AI is
 * unreachable or returns an error, the submission is still written to KV and
 * the visitor is still told it went through, because from their side it did.
 * A failed CRM call is our problem to reconcile, not theirs to retry.
 *
 * Environment (set in Cloudflare Pages, Settings, Environment variables.
 * Mark the two secrets as encrypted. None of them belong in this repo):
 *   DAY_WEBHOOK_URL   required   Day AI inbound webhook or API endpoint
 *   DAY_API_KEY       optional   sent as Authorization: Bearer if present
 *   NOTIFY_EMAIL      optional   fallback copy, defaults to hello@optiadata.com
 *   RESEND_API_KEY    optional   enables the email fallback
 * Bindings:
 *   LEADS             optional   KV namespace, stores every submission
 */

const MAX = { name: 120, company: 160, email: 200, message: 5000 };

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    },
  });

/* Deliberately loose. Address validity is decided by whether a reply arrives,
   not by a regex, and every clever pattern rejects somebody's real address. */
const looksLikeEmail = (v) => /^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$/.test(v);

export async function onRequestPost({ request, env, waitUntil }) {
  let form;
  try {
    const ct = request.headers.get('content-type') || '';
    form = ct.includes('application/json')
      ? await request.json()
      : Object.fromEntries(await request.formData());
  } catch {
    return json(400, { ok: false, error: 'Could not read the submission.' });
  }

  /* Spam screening. Both checks are silent: a bot that is told why it failed
     is a bot that comes back fixed. Return the success shape instead. */
  if (form.website) return json(200, { ok: true });            // honeypot
  const elapsed = Date.now() - Number(form.t || 0);
  if (!form.t || elapsed < 2500 || elapsed > 86400000) return json(200, { ok: true });

  const clean = (v, n) => String(v ?? '').trim().slice(0, n);
  const lead = {
    name: clean(form.name, MAX.name),
    company: clean(form.company, MAX.company),
    email: clean(form.email, MAX.email),
    message: clean(form.message, MAX.message),
  };

  const missing = Object.keys(lead).filter((k) => !lead[k]);
  if (missing.length) return json(422, { ok: false, error: 'Please complete every field.', missing });
  if (!looksLikeEmail(lead.email)) return json(422, { ok: false, error: 'That email address does not look right.', missing: ['email'] });

  const meta = {
    receivedAt: new Date().toISOString(),
    source: 'optiadata.com contact form',
    page: clean(form.page, 300),
    country: request.headers.get('cf-ipcountry') || null,
    userAgent: clean(request.headers.get('user-agent'), 300),
  };
  const id = `lead:${meta.receivedAt}:${crypto.randomUUID().slice(0, 8)}`;
  /* The reference travels with the lead so a row in the destination can be
     matched back to a log line when someone says they never got a reply. */
  const record = { ...lead, ...meta, reference: id };

  /* Store before responding, so the enquiry is durable even if everything
     downstream fails. A KV write is tens of milliseconds; the delivery that
     follows is not, which is why only this part is awaited. */
  if (env.LEADS) {
    try {
      await env.LEADS.put(id, JSON.stringify({ ...record, delivered: false }), {
        expirationTtl: 60 * 60 * 24 * 365,
      });
    } catch { /* storage is a safety net, never the reason a lead is rejected */ }
  }

  /* Delivery runs after the response. Google Apps Script took 38 seconds to
     answer in testing, and blocking on it meant the visitor watched "Sending."
     for most of a minute, long enough to give up or submit again. Nothing in
     the reply depends on the outcome: the lead is already stored, and whether
     the spreadsheet accepted it is our problem to reconcile, not theirs to
     wait for. */
  async function deliver() {
  let delivered = false;
  let failure = null;

  const endpoint = env.LEAD_WEBHOOK_URL || env.DAY_WEBHOOK_URL;

  if (endpoint) {
    try {
      const headers = { 'content-type': 'application/json' };
      const key = env.LEAD_API_KEY || env.DAY_API_KEY;
      if (key) headers.authorization = `Bearer ${key}`;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(record),
      });

      /* A 200 is not proof of delivery. Google Apps Script answers 200 to
         everything, including its own rejection path and the sign-in page it
         serves when a web app is not shared publicly. Trusting the status
         alone made two different failures look identical to success and left
         the sheet silently empty. So: read the body, and require the endpoint
         to say so. Anything that cannot be parsed as an acknowledgement is
         treated as a failure, which is the safe direction to be wrong in. */
      const text = (await res.text()).slice(0, 500);
      let ack = null;
      try { ack = JSON.parse(text); } catch { /* not JSON, handled below */ }

      if (!res.ok) {
        failure = `endpoint responded ${res.status}: ${text.slice(0, 120)}`;
      } else if (ack && ack.ok === true) {
        delivered = true;
      } else if (ack && ack.ok === false) {
        failure = `endpoint rejected the lead: ${text.slice(0, 120)}`;
      } else {
        failure = `endpoint returned 200 but no {"ok":true}: ${text.slice(0, 120)}`;
      }
    } catch (e) {
      failure = `endpoint unreachable: ${e.message}`;
    }
  } else {
    failure = 'no LEAD_WEBHOOK_URL or DAY_WEBHOOK_URL configured';
  }

  /* Email fallback, only when the CRM did not take it. */
  if (!delivered && env.RESEND_API_KEY) {
    const to = env.NOTIFY_EMAIL || 'hello@optiadata.com';
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          authorization: `Bearer ${env.RESEND_API_KEY}`,
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          from: 'Optia website <website@optiadata.com>',
          to: [to],
          reply_to: lead.email,
          subject: `Website enquiry: ${lead.name}, ${lead.company}`,
          text:
            `${lead.name} at ${lead.company}\n${lead.email}\n\n` +
            `${lead.message}\n\n---\nReceived ${meta.receivedAt}\n` +
            `Not delivered to the lead store: ${failure}\nReference ${id}`,
        }),
      });
    } catch { /* the KV record is still the backstop */ }
  }

  if (env.LEADS && delivered) {
    try {
      await env.LEADS.put(id, JSON.stringify({ ...record, delivered: true }), {
        expirationTtl: 60 * 60 * 24 * 365,
      });
    } catch { /* nothing actionable */ }
  }

  if (!delivered) console.error('contact form lead not delivered', { id, failure });
  }

  /* waitUntil keeps the worker alive for delivery after the response is sent.
     Without it, awaiting would put the endpoint's latency in front of the
     visitor; falling back to await keeps the function correct anywhere the
     runtime does not provide it. */
  if (typeof waitUntil === 'function') waitUntil(deliver());
  else await deliver();

  /* Always 200 on a valid submission. The visitor did their part. */
  return json(200, { ok: true, reference: id });
}

/* No catch-all handler on purpose. With only onRequestPost exported, Pages
   answers every other method with 405 itself. Exporting onRequest as well
   would leave which one wins ambiguous. */
