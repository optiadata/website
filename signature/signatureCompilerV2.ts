/**
 * Optia Data signature, version 2.
 *
 * Drop-in replacement for src/utils/signatureCompiler.ts in
 * optiadata/signature_optia. Same SignatureConfig in, new markup out, so the
 * builder's form does not need to change.
 *
 * What changed from v1, and why:
 *
 *  - The logo is no longer a data: URI. Gmail and Outlook both refuse to
 *    render those, so v1's logo is invisible for most recipients. v2 points at
 *    a hosted PNG.
 *  - Borna and #3E4899 are gone. The current brand is Ultraviolet #4828E5 and
 *    Switzer, and the site's hero reads "Intelligence. Built for Decisions."
 *  - Webfonts cannot load in email, so the brand statement is set once as an
 *    image where the real typeface survives, and every detail a recipient
 *    actually needs stays as live text in a web-safe stack. A client that
 *    blocks images still shows a working signature.
 *  - The dotted divider is dropped. It relied on a run of bullet characters,
 *    which wraps unpredictably and reads as damage in narrow windows.
 */

import { SignatureConfig } from '../types';

/** 2x asset served at 1x dimensions, so it stays sharp on retina.
 *  Move this to https://optiadata.com/signature/ when the domain can host it. */
export const STRIP_URL =
  'https://optiadata.github.io/website/signature/optia-signature-strip-2x.png';
export const STRIP_W = 520;
export const STRIP_H = 104;

const UV = '#4828E5';
const INK = '#05070D';
const MUTED = '#5C5C68';
const FAINT = '#8A8A95';
const RULE = '#C9C9D2';

/** Web-safe only. Anything else silently falls back and ruins the metrics. */
const STACK = 'Arial,Helvetica,sans-serif';

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function compileHTMLSignatureV2(config: SignatureConfig): string {
  const {
    fullName, jobTitle, companyName, email, mobile, website, disclaimer,
  } = config;

  const site = website?.trim() || 'https://optiadata.com';
  const href = site.startsWith('http') ? site : `https://${site}`;
  const label = site.replace(/^(https?:\/\/)?(www\.)?/, '').replace(/\/$/, '');
  const row = (inner: string) => `\n  <tr>\n    <td ${inner}\n    </td>\n  </tr>`;

  let html =
`<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; font-family:${STACK}; color:${INK}; max-width:${STRIP_W}px;">`;

  html += row(`style="padding:0 0 3px 0; font-family:${STACK}; font-size:17px; font-weight:bold; line-height:1.25; color:${INK};">
      ${esc(fullName)}`);

  if (jobTitle || companyName) {
    const sep = jobTitle && companyName
      ? `&nbsp;&nbsp;<span style="color:${RULE};">|</span>&nbsp;&nbsp;` : '';
    html += row(`style="padding:0 0 13px 0; font-family:${STACK}; font-size:13px; line-height:1.4; color:${MUTED};">
      ${esc(jobTitle || '')}${sep}${esc(companyName || '')}`);
  }

  const lines: string[] = [];
  if (email) {
    lines.push(`<a href="mailto:${esc(email)}" style="color:${UV}; text-decoration:none;">${esc(email)}</a>`);
  }
  if (mobile) {
    lines.push(`<a href="tel:${mobile.replace(/[^\d+]/g, '')}" style="color:${INK}; text-decoration:none;">${esc(mobile)}</a>`);
  }
  lines.push(`<a href="${esc(href)}" style="color:${UV}; text-decoration:none;">${esc(label)}</a>`);
  html += row(`style="padding:0 0 15px 0; font-family:${STACK}; font-size:13px; line-height:1.75; color:${INK};">
      ${lines.join('\n      <br>\n      ')}`);

  // width and height as attributes as well as CSS: Outlook renders through
  // Word and ignores CSS sizing on images.
  html += row(`style="padding:0 0 13px 0; line-height:0;">
      <a href="${esc(href)}" style="text-decoration:none;">
        <img src="${STRIP_URL}" width="${STRIP_W}" height="${STRIP_H}" alt="${esc(companyName || 'Optia Data')}. Intelligence. Built for Decisions." style="display:block; border:0; outline:none; text-decoration:none; width:${STRIP_W}px; height:${STRIP_H}px;">
      </a>`);

  const foot = ['ISO 27001:2022 certified'];
  if (disclaimer) foot.push(esc(disclaimer));
  html += row(`style="font-family:${STACK}; font-size:10px; line-height:1.5; color:${FAINT};">
      ${foot.join('\n      <br><br>\n      ')}`);

  return `${html}\n</table>`;
}

export function compilePlainTextSignatureV2(config: SignatureConfig): string {
  const { fullName, jobTitle, companyName, mobile, email, website, disclaimer } = config;
  const label = (website || 'optiadata.com').replace(/^(https?:\/\/)?(www\.)?/, '').replace(/\/$/, '');
  const out = [fullName];
  if (jobTitle || companyName) out.push([jobTitle, companyName].filter(Boolean).join(' | '));
  out.push('');
  if (email) out.push(email);
  if (mobile) out.push(mobile);
  out.push(label, '', `${companyName || 'Optia Data'}. Intelligence. Built for Decisions.`,
           'ISO 27001:2022 certified');
  if (disclaimer) out.push('', disclaimer);
  return out.join('\n');
}
