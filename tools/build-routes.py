# -*- coding: utf-8 -*-
"""Pre-render one real HTML file per route.

Why this exists
---------------
v7 was a single document with a fragment router. A fragment is never sent to
the server, so every crawler and every social scraper saw the same homepage no
matter which URL it was given. Fifteen case studies existed for people and did
not exist for search, and pasting one into LinkedIn produced the homepage card.

This script takes v7/index.html as the single source of truth and writes a
finished file per route: the right section already active, the right title,
description, canonical and social card in the head, and JSON-LD describing what
the page actually is. The client-side router still runs, so navigation between
pages stays instant; the difference is that a cold hit now arrives complete
instead of depending on JavaScript to assemble itself.

Everything is derived from the markup rather than restated here. The client
name, the headline, the summary and the hero image all already exist in the
case study itself, so a copy change in index.html flows through on the next
build and cannot drift out of step.

Idempotent: safe to run repeatedly. Generated files are overwritten and the
injected block in index.html sits between sentinels that are stripped first.

Usage:  python tools/build-routes.py
"""
import io
import json
import os
import re
import sys
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V7 = os.path.join(ROOT, "v7")
SRC = os.path.join(V7, "index.html")
ORIGIN = "https://optiadata.com"

# Kept in the same order as the ROUTES map inside index.html. If the two ever
# disagree the check at the bottom of this file fails the build rather than
# quietly shipping a page nothing links to.
ROUTES = [
    ("/about/", "about-page"),
    ("/privacy/", "privacy-policy"),
    ("/case-studies/", "case-index"),
    ("/case-studies/arla-foods/", "case-arla"),
    ("/case-studies/campari/", "case-campari"),
    ("/case-studies/starbucks-emea/", "case-starbucks"),
    ("/case-studies/bacardi/", "case-bacardi"),
    ("/case-studies/australian-vintage/", "case-australian-vintage"),
    ("/case-studies/golden-acre-foods/", "case-golden-acre"),
    ("/case-studies/samworth-brothers/", "case-samworth"),
    ("/case-studies/vit-hit/", "case-vithit"),
    ("/case-studies/international-beverage/", "case-international-beverage"),
    ("/case-studies/samyang-foods/", "case-samyang"),
    ("/case-studies/qts-data-centres/", "case-qts"),
    ("/case-studies/inspired-learning-group/", "case-ilg"),
    ("/case-studies/henkel/", "case-henkel"),
    ("/case-studies/tier-one-global-bank/", "case-tier-one-bank"),
    ("/case-studies/oracare-group/", "case-oracare"),
]

# The three non-case routes need copy of their own: there is no hero summary to
# lift, and a description Google truncates mid-sentence is worse than none.
STATIC_META = {
    "case-index": (
        "Case studies",
        "Fifteen engagements across food, drink, retail, education, engineering, "
        "financial services and data centres, each showing the problem, what we "
        "changed and what happened next.",
    ),
    "about-page": (
        "About",
        "The story behind Optia, in our founder's own words. Why we think the "
        "human is the point, and how that shapes the way we build reporting.",
    ),
    "privacy-policy": (
        "Privacy Policy",
        "How Optia Data collects, uses and protects personal information, and "
        "how to exercise your rights under UK GDPR.",
    ),
}

SENTINEL_OPEN = "<!-- build-routes:jsonld -->"
SENTINEL_CLOSE = "<!-- /build-routes:jsonld -->"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def text_of(fragment):
    """Markup to plain readable text, for use in meta tags and JSON-LD."""
    t = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", unescape(t)).strip()


def attr(value):
    """Escape for an HTML attribute. Order matters: ampersand first."""
    return (value.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def section_slice(doc, section_id):
    """Return (start, end) of a top-level <section id="..."> including its
    closing tag. Scanned rather than regexed because a case page may contain
    nested <section> elements and a lazy match would stop at the first one."""
    m = re.search(r'<section[^>]*\bid="%s"[^>]*>' % re.escape(section_id), doc)
    if not m:
        raise SystemExit("no section with id=%r" % section_id)
    depth, i = 0, m.start()
    for tag in re.finditer(r"</?section\b", doc[m.start():]):
        depth += 1 if tag.group(0) == "<section" else -1
        if depth == 0:
            i = m.start() + tag.end()
            break
    else:
        raise SystemExit("unbalanced <section> around id=%r" % section_id)
    return m.start(), doc.index(">", i) + 1


def replace_meta(head, pattern, replacement):
    new, n = re.subn(pattern, lambda _: replacement, head, count=1)
    if not n:
        raise SystemExit("head tag not found, pattern: %s" % pattern)
    return new


# ---------------------------------------------------------------------------
# read the source and pull out what each route needs
# ---------------------------------------------------------------------------

doc = io.open(SRC, encoding="utf-8", newline="").read()

home_title = re.search(r"<title>(.*?)</title>", doc, re.S).group(1).strip()
js_title = re.search(r"var BASE_TITLE = '([^']+)'", doc)
if not js_title:
    raise SystemExit("BASE_TITLE literal not found in the router")
if js_title.group(1) != home_title:
    raise SystemExit(
        "BASE_TITLE and <title> disagree, so navigating home would show the "
        "wrong title:\n  <title>    %r\n  BASE_TITLE %r" % (home_title, js_title.group(1))
    )

home_desc = text_of(re.search(r'<meta name="description" content="([^"]*)"', doc).group(1))

# Client names live in the case index tiles, keyed by the path they link to.
tiles = {}
for m in re.finditer(r'<a[^>]*class="[^"]*case-tile[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', doc, re.S):
    client = re.search(r'case-tile__client[^>]*>(.*?)<', m.group(2), re.S)
    if client:
        tiles[m.group(1)] = text_of(client.group(1))

meta_for = {}
for path, sid in ROUTES:
    if sid in STATIC_META:
        name, desc = STATIC_META[sid]
        meta_for[sid] = {"name": name, "title": "%s, Optia Data" % name, "desc": desc,
                         "headline": name, "client": None, "image": None, "kind": "page"}
        continue

    start, end = section_slice(doc, sid)
    block = doc[start:end]
    client = tiles.get(path)
    if not client:
        raise SystemExit("no case index tile links to %s, so it has no client name" % path)

    h1 = re.search(r'case-hero__title">(.*?)</h1>', block, re.S)
    sub = re.search(r'case-hero__sub">(.*?)</p>', block, re.S)
    img = re.search(r'case-hero__img"[^>]*\bdata-src="([^"]+)"', block)
    sector = re.search(r'case-hero__eyebrow">(.*?)<', block, re.S)
    if not (h1 and sub):
        raise SystemExit("%s is missing a hero title or summary" % sid)

    meta_for[sid] = {
        "name": client,
        "title": "%s case study, Optia Data" % client,
        "desc": text_of(sub.group(1)),
        "headline": text_of(h1.group(1)),
        "client": client,
        "sector": text_of(sector.group(1)) if sector else None,
        # The social card is rendered from this page's own hero by
        # tools/build-og-cards.py, so the filename is predictable from the path.
        # The confidential engagement has no hero image and falls back to the
        # generic card rather than borrowing somebody else's photograph.
        "image": ("/images/og/%s.jpg" % path.strip("/").split("/")[-1]) if img else None,
        "kind": "case",
    }


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------

ORG_REF = {"@id": "%s/#organisation" % ORIGIN}
SITE_REF = {"@id": "%s/#website" % ORIGIN}


def org_node(full):
    """A compact Organization so every page's publisher reference resolves on
    its own. The full record, with company number, areas served and the rest,
    stays in /company-data/ rather than being repeated eighteen times."""
    node = {
        "@type": "Organization",
        "@id": ORG_REF["@id"],
        "name": "Optia Data",
        "url": ORIGIN + "/",
        "logo": {
            "@type": "ImageObject",
            "@id": "%s/#logo" % ORIGIN,
            "url": "%s/images/optia-logo.svg" % ORIGIN,
            "contentUrl": "%s/images/optia-logo.svg" % ORIGIN,
            "caption": "Optia Data",
            "width": 221,
            "height": 89,
        },
    }
    if full:
        node.update({
            "legalName": "Optia Data Ltd",
            "description": home_desc,
            "email": "hello@optiadata.com",
            "foundingDate": "2024-08-07",
            "address": {"@type": "PostalAddress", "addressLocality": "Oxfordshire",
                        "addressCountry": "GB"},
            "identifier": [{"@type": "PropertyValue",
                            "propertyID": "GB Companies House company number",
                            "value": "15884308"}],
            "sameAs": [
                "https://www.linkedin.com/company/optia-data/",
                "https://find-and-update.company-information.service.gov.uk/company/15884308",
                "https://microsites.nielseniq.com/partnernetwork/apps/optia-data/",
            ],
        })
    return node


def crumbs(path, label):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": ORIGIN + "/"}]
    if path.startswith("/case-studies/") and path != "/case-studies/":
        items.append({"@type": "ListItem", "position": 2, "name": "Case studies",
                      "item": "%s/case-studies/" % ORIGIN})
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": label,
                  "item": ORIGIN + path})
    return {"@type": "BreadcrumbList", "@id": "%s%s#breadcrumb" % (ORIGIN, path),
            "itemListElement": items}


def graph_for(path, sid):
    url = ORIGIN + path
    is_home = sid is None
    m = ({"title": home_title, "desc": home_desc, "name": "Optia Data",
          "headline": home_title, "kind": "home", "image": None}
         if is_home else meta_for[sid])

    page = {
        "@type": "WebPage",
        "@id": "%s#webpage" % url,
        "url": url,
        "name": m["title"],
        "description": m["desc"],
        "isPartOf": SITE_REF,
        "inLanguage": "en-GB",
        "about": ORG_REF,
    }
    nodes = [
        org_node(full=is_home),
        {"@type": "WebSite", "@id": SITE_REF["@id"], "url": ORIGIN + "/",
         "name": "Optia Data", "publisher": ORG_REF, "inLanguage": "en-GB"},
        page,
    ]

    if not is_home:
        page["breadcrumb"] = {"@id": "%s#breadcrumb" % url}
        nodes.append(crumbs(path, m["name"]))

    if not is_home and m["kind"] == "case":
        article = {
            "@type": "Article",
            "@id": "%s#article" % url,
            "headline": m["headline"],
            "description": m["desc"],
            "url": url,
            "isPartOf": {"@id": "%s#webpage" % url},
            "mainEntityOfPage": {"@id": "%s#webpage" % url},
            "author": ORG_REF,
            "publisher": ORG_REF,
            "inLanguage": "en-GB",
            # The named party is the subject of the piece, not its author. Every
            # name here is one the site already publishes; the confidential
            # engagement carries only the label it is published under.
            "about": {"@type": "Organization", "name": m["client"]},
        }
        if m.get("sector"):
            article["articleSection"] = m["sector"]
        if m["image"]:
            article["image"] = ORIGIN + m["image"]
        nodes.append(article)

    return {"@context": "https://schema.org", "@graph": nodes}


def ld_block(path, sid):
    body = json.dumps(graph_for(path, sid), indent=2, ensure_ascii=False)
    return "%s\n<script type=\"application/ld+json\">\n%s\n</script>\n%s" % (
        SENTINEL_OPEN, body, SENTINEL_CLOSE)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def strip_injected(html):
    return re.sub(re.escape(SENTINEL_OPEN) + r".*?" + re.escape(SENTINEL_CLOSE),
                  "", html, flags=re.S).replace("\n\n\n", "\n\n")


def rewrite_head(html, path, sid):
    """Swap the homepage's own meta for this route's. The head is sliced out
    first so a stray match further down a 700KB document cannot be hit."""
    m = meta_for[sid]
    url = ORIGIN + path
    title = m["title"]
    desc = m["desc"]
    image = ORIGIN + (m["image"] or "/images/og-card.jpg")
    alt = "%s, an Optia case study" % m["name"] if m["kind"] == "case" else "Optia"

    cut = html.index("</head>")
    head, rest = html[:cut], html[cut:]

    head = replace_meta(head, r"<title>.*?</title>", "<title>%s</title>" % attr(title))
    head = replace_meta(head, r'<meta name="description" content="[^"]*">',
                        '<meta name="description" content="%s">' % attr(desc))
    head = replace_meta(head, r'<link rel="canonical" href="[^"]*">',
                        '<link rel="canonical" href="%s">' % url)
    head = replace_meta(head, r'<meta property="og:type" content="[^"]*">',
                        '<meta property="og:type" content="%s">'
                        % ("article" if m["kind"] == "case" else "website"))
    head = replace_meta(head, r'<meta property="og:title" content="[^"]*">',
                        '<meta property="og:title" content="%s">' % attr(title))
    head = replace_meta(head, r'<meta property="og:description" content="[^"]*">',
                        '<meta property="og:description" content="%s">' % attr(desc))
    head = replace_meta(head, r'<meta property="og:url" content="[^"]*">',
                        '<meta property="og:url" content="%s">' % url)
    head = replace_meta(head, r'<meta property="og:image" content="[^"]*">',
                        '<meta property="og:image" content="%s">' % image)
    head = replace_meta(head, r'<meta property="og:image:alt" content="[^"]*">',
                        '<meta property="og:image:alt" content="%s">' % attr(alt))
    head = replace_meta(head, r'<meta name="twitter:title" content="[^"]*">',
                        '<meta name="twitter:title" content="%s">' % attr(title))
    head = replace_meta(head, r'<meta name="twitter:description" content="[^"]*">',
                        '<meta name="twitter:description" content="%s">' % attr(desc))
    head = replace_meta(head, r'<meta name="twitter:image" content="[^"]*">',
                        '<meta name="twitter:image" content="%s">' % image)
    return head + rest


def activate(html, sid):
    """Open the document on the right section, exactly as the router would."""
    start, end = section_slice(html, sid)
    block = html[start:end]
    open_tag = re.match(r"<section[^>]*>", block).group(0)
    new_open = (open_tag.replace('class="', 'class="is-active ', 1)[:-1] + ' role="main">')
    # Images inside the active section are held as data-src so that landing on
    # a case study does not also pull down the homepage's photography. This is
    # the one section that is definitely visible, so its images become real.
    block = new_open + block[len(open_tag):]
    block = block.replace(' data-src="', ' src="')

    light = "case-study" not in open_tag
    html = html[:start] + block + html[end:]
    html = html.replace(
        '<html lang="en-GB">',
        '<html lang="en-GB" class="routing-case%s">' % (" routing-case--light" if light else ""),
        1)
    return html


base = strip_injected(doc)
if base != doc:
    io.open(SRC, "w", encoding="utf-8", newline="").write(base)

written = []
for path, sid in ROUTES:
    html = rewrite_head(base, path, sid)
    html = activate(html, sid)
    html = html.replace("</head>", ld_block(path, sid) + "\n</head>", 1)
    out = os.path.join(V7, path.strip("/").replace("/", os.sep), "index.html")
    os.path.isdir(os.path.dirname(out)) or os.makedirs(os.path.dirname(out))
    io.open(out, "w", encoding="utf-8", newline="").write(html)
    written.append((path, sid, len(html)))

# The homepage is the source file, so it is only given its graph, nothing else.
io.open(SRC, "w", encoding="utf-8", newline="").write(
    base.replace("</head>", ld_block("/", None) + "\n</head>", 1))


# ---------------------------------------------------------------------------
# sitemap
# ---------------------------------------------------------------------------

urls = [(ORIGIN + "/", "1.0")]
urls += [(ORIGIN + p, "0.9" if p.startswith("/case-studies/") else "0.6")
         for p, _ in ROUTES if p != "/privacy/"]
urls += [("%s/company-data/" % ORIGIN, "0.5"), ("%s/privacy/" % ORIGIN, "0.2")]

sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
           "<!-- Generated by tools/build-routes.py. Do not edit by hand. -->",
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, pri in urls:
    sitemap.append("  <url>\n    <loc>%s</loc>\n    <priority>%s</priority>\n  </url>" % (u, pri))
sitemap.append("</urlset>\n")
io.open(os.path.join(V7, "sitemap.xml"), "w", encoding="utf-8", newline="").write(
    "\n".join(sitemap))


# ---------------------------------------------------------------------------
# report, and the consistency check that makes this safe to re-run
# ---------------------------------------------------------------------------

js_routes = dict(re.findall(r"'(/[a-z0-9/-]*/)':\s*'([a-z0-9-]+)'",
                            doc[doc.index("var ROUTES = {"):doc.index("var PATH_FOR")]))
if js_routes != dict(ROUTES):
    only_js = set(js_routes) - {p for p, _ in ROUTES}
    only_py = {p for p, _ in ROUTES} - set(js_routes)
    raise SystemExit("ROUTES in index.html and build-routes.py disagree.\n"
                     "  only in index.html: %s\n  only in this script: %s"
                     % (sorted(only_js) or "-", sorted(only_py) or "-"))

print("built %d pages from %s\n" % (len(written), os.path.basename(SRC)))
for path, sid, size in written:
    m = meta_for[sid]
    print("  %-42s %-28s %5.0fKB  %s" % (path, sid, size / 1024,
                                         "card" if m["image"] else "generic card"))
print("\nsitemap.xml: %d URLs" % len(urls))
print("route table: index.html and this script agree on all %d routes" % len(ROUTES))
