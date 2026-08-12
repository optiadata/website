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

export async function onRequestPost({ request, env }) {
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
  const record = { ...lead, ...meta };
  const id = `lead:${meta.receivedAt}:${crypto.randomUUID().slice(0, 8)}`;

  /* Store first, deliver second, so a CRM outage cannot lose the enquiry. */
  if (env.LEADS) {
    try {
      await env.LEADS.put(id, JSON.stringify({ ...record, delivered: false }), {
        expirationTtl: 60 * 60 * 24 * 365,
      });
    } catch { /* storage is a safety net, never the reason a lead is rejected */ }
  }

  let delivered = false;
  let failure = null;

  if (env.DAY_WEBHOOK_URL) {
    try {
      const headers = { 'content-type': 'application/json' };
      if (env.DAY_API_KEY) headers.authorization = `Bearer ${env.DAY_API_KEY}`;
      const res = await fetch(env.DAY_WEBHOOK_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify(record),
      });
      delivered = res.ok;
      if (!res.ok) failure = `Day AI responded ${res.status}`;
    } catch (e) {
      failure = `Day AI unreachable: ${e.message}`;
    }
  } else {
    failure = 'DAY_WEBHOOK_URL is not configured';
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
            `Not delivered to Day AI: ${failure}\nReference ${id}`,
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

  if (!delivered) console.error('contact form not delivered to CRM', { id, failure });

  /* Always 200 on a valid submission. The visitor did their part. */
  return json(200, { ok: true, reference: id });
}

/* No catch-all handler on purpose. With only onRequestPost exported, Pages
   answers every other method with 405 itself. Exporting onRequest as well
   would leave which one wins ambiguous. */
