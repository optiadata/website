# Optia Data email signature

Replaces the Borna / `#3E4899` signature in `optiadata/signature_optia`, which
predates the current site. This one uses Ultraviolet `#4828E5`, the live hero
line, and the same composition as the LinkedIn covers.

## Before anyone installs it

**The image must be live at a public URL or every signature ships broken.**
`signature.html` currently points at:

```
https://optiadata.github.io/website/signature/optia-signature-strip-2x.png
```

That resolves once this folder is committed and pushed to the `website` repo.
Better long term: host it on `optiadata.com/signature/` and change the one
`src` in `signature.html`, so the asset sits on the domain the brand owns and
survives any change to where the site is hosted.

Never inline the image as a `data:` URI. Gmail and Outlook both refuse to
render them, which is a live bug in the old builder's `signatureCompiler.ts`.

## Installing

1. Open `signature.html` in a browser.
2. Select the whole signature and copy it.
3. Paste into your client's signature box:
   - **Gmail** — Settings, See all settings, Signature
   - **Outlook web** — Settings, Mail, Compose and reply
   - **Outlook desktop** — File, Options, Mail, Signatures
   - **Apple Mail** — Settings, Signatures, and untick "Always match my default message font"

Change the five values marked `CHANGE ME`: name, role, email, phone, and the
`tel:` link. Delete the phone line and its `<br>` if you would rather not
publish a mobile.

## Why it is built this way

Email clients do not load webfonts, so Switzer and Zodiak cannot render as live
text. Everything a recipient needs is therefore real text in a web-safe stack,
and only the brand statement is an image, where the actual typeface survives.
If a client blocks images, nothing load-bearing is lost.

The image is a 2x file served at 1x dimensions so it stays sharp on retina.
Width and height are set as HTML attributes as well as in CSS, because Outlook
renders through Word and ignores CSS sizing on images.

## Plain text version

For clients that strip HTML:

```
Helena Carre
Innovation Marketing and Insights Engineer | Optia Data

helena@optiadata.com
+44 0000 000000
optiadata.com

Optia Data. Intelligence. Built for Decisions.
ISO 27001:2022 certified

This electronic message transmission contains information from Optia Data which
may be confidential or privileged. If you are not the intended recipient, be
aware that any disclosure, copying, distribution or use of the contents of this
information is prohibited.
```

## Files

| File | Notes |
| --- | --- |
| `signature.html` | The signature. Copy from a browser, not from the source. |
| `optia-signature-strip-2x.png` | 1040x208. The one referenced by the HTML. |
| `optia-signature-strip.png` | 520x104. Only for clients that mangle 2x images. |

## Still open

- The old builder at `optiadata/signature_optia` still emits the previous brand.
  This markup can be dropped into its `signatureCompiler.ts` so the builder
  produces the new signature for everyone, rather than each person pasting HTML.
- The old slogan, "Knowledge made visible. Insights made accessible.", is not on
  the current site. This uses the live hero instead.
