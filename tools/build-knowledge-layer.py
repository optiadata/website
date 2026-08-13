# -*- coding: utf-8 -*-
"""
Generate the Optia Data machine-readable knowledge layer from v7/data/company.json.

The site has no build step, so this is run by hand. Re-run it after any edit to
company.json, otherwise the page, its JSON-LD and llms.txt drift apart.

Outputs
  v7/company-data/index.html   company information page, with one JSON-LD @graph
  v7/llms.txt                  curated Markdown index for answer engines

Reads, but never writes, v7/index.html: the @font-face blocks and the :root token
block are lifted from it verbatim so this page introduces no new font, no new
colour and no new spacing token.
"""
import io, json, os, re, sys

# Derived from this file's location, so the script works in any checkout,
# including a git worktree.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V7   = os.path.join(ROOT, "v7")
SRC  = os.path.join(V7, "index.html")
DATA = os.path.join(V7, "data", "company.json")

# Only the weights this page actually uses, lifted verbatim from v7/index.html.
WANT_FONTS = [("Switzer", "400"), ("Switzer", "500"), ("Switzer", "600"), ("Zodiak", "400")]


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def load_source_css():
    h = io.open(SRC, encoding="utf-8").read()
    faces = []
    for block in re.findall(r"@font-face\{[^}]*\}", h):
        fam = re.search(r"font-family:'([^']+)'", block).group(1)
        w = re.search(r"font-weight:\s*([^;}]+)", block)
        st = re.search(r"font-style:\s*([^;}]+)", block)
        w = w.group(1).strip() if w else "400"
        st = st.group(1).strip() if st else "normal"
        if st == "normal" and (fam, w) in WANT_FONTS:
            faces.append(block)
    root = re.search(r":root \{(.*?)\n\}", h, re.S).group(1)
    tokens = "\n".join(
        "  %s: %s;" % (k, v.strip())
        for k, v in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", root)
    )
    return faces, tokens


def url_for(site, path):
    return site["origin"].rstrip("/") + path


def case_url(site, cs):
    """Absolute URL for a case study.

    Each case study carries its own path since real URLs shipped. Building the
    URL from a pattern and a fragment id, as this did, now produces a link to
    a page that does not exist.
    """
    if isinstance(cs, dict) and cs.get("path"):
        return site["origin"].rstrip("/") + cs["path"]
    raise SystemExit("case study %r has no path; re-run after updating company.json"
                     % (cs.get("id") if isinstance(cs, dict) else cs))


# --------------------------------------------------------------------------- #
#  JSON-LD: one @graph, @id-linked, nothing that is not on the visible page
# --------------------------------------------------------------------------- #
def build_graph(d):
    site, c = d["site"], d["company"]
    origin = site["origin"].rstrip("/")
    page = url_for(site, site["knowledgePagePath"])
    org_id, site_id, page_id = origin + "/#organisation", origin + "/#website", page + "#webpage"

    org = {
        "@type": "Organization",
        "@id": org_id,
        "name": c["name"],
        "legalName": c["legalName"],
        "alternateName": c["alternateName"],
        "url": origin + c["url"],
        "logo": {
            "@type": "ImageObject",
            "@id": origin + "/#logo",
            "url": origin + c["logo"],
            "contentUrl": origin + c["logo"],
            "caption": c["name"],
            "width": 221,
            "height": 89,
        },
        "image": {"@id": origin + "/#logo"},
        "description": c["description"],
        "foundingDate": c["founded"],
        "email": c["email"],
        "identifier": [{
            "@type": "PropertyValue",
            "propertyID": "GB Companies House company number",
            "value": c["companyNumber"],
        }],
        "address": {
            "@type": "PostalAddress",
            "addressLocality": c["address"]["addressLocality"],
            "addressCountry": c["address"]["addressCountry"],
        },
        "areaServed": [{"@type": "Country", "name": a} for a in c["areaServed"]],
        "knowsAbout": d["expertise"] + d["methodologies"] + d["dataSources"],
        "sameAs": d["socialProfiles"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Optia Data services",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": page + "#service-" + s["id"]}}
                                for s in d["services"]],
        },
    }
    if d["certifications"]:
        org["hasCredential"] = [{"@type": "EducationalOccupationalCredential",
                                 "credentialCategory": "certification",
                                 "name": x["name"]} for x in d["certifications"]]

    graph = [org, {
        "@type": "WebSite",
        "@id": site_id,
        "url": origin + "/",
        "name": c["name"],
        "publisher": {"@id": org_id},
        "inLanguage": "en-GB",
    }, {
        "@type": "WebPage",
        "@id": page_id,
        "url": page,
        "name": "Optia Data, company information",
        "description": "Structured company information for Optia Data: what it does, the data it works with, the industries it serves, and the published case studies behind each claim.",
        "isPartOf": {"@id": site_id},
        "about": {"@id": org_id},
        "inLanguage": "en-GB",
        "datePublished": d["lastUpdated"],
        "dateModified": d["lastUpdated"],
    }, {
        "@type": "BreadcrumbList",
        "@id": page + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Optia Data", "item": origin + "/"},
            {"@type": "ListItem", "position": 2, "name": "Company information", "item": page},
        ],
    }]

    for s in d["services"]:
        graph.append({
            "@type": "Service",
            "@id": page + "#service-" + s["id"],
            "name": s["name"],
            "description": s["description"],
            "provider": {"@id": org_id},
            "serviceType": s["name"],
            "areaServed": [{"@type": "Country", "name": a} for a in c["areaServed"]],
        })

    graph.append({
        "@type": "FAQPage",
        "@id": page + "#faq",
        "isPartOf": {"@id": page_id},
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in d["faq"]],
    })

    return {"@context": "https://schema.org", "@graph": graph}


# --------------------------------------------------------------------------- #
#  Page
# --------------------------------------------------------------------------- #
def build_page(d, faces, tokens):
    site, c = d["site"], d["company"]
    origin = site["origin"].rstrip("/")
    page = url_for(site, site["knowledgePagePath"])
    graph = json.dumps(build_graph(d), indent=2, ensure_ascii=False)

    def sec(title, inner, sid):
        return ('<section class="kp-section" id="%s">\n<h2>%s</h2>\n%s\n</section>'
                % (sid, esc(title), inner))

    services = "\n".join(
        '<div class="kp-item"><h3>%s</h3><p>%s</p></div>' % (esc(s["name"]), esc(s["description"]))
        for s in d["services"])

    facts = [
        ("Legal name", esc(c["legalName"])),
        ("Trading name", esc(c["name"])),
        ("Company registration number", esc(c["companyNumber"]) +
         ' (<a href="https://find-and-update.company-information.service.gov.uk/company/%s">Companies House</a>)' % esc(c["companyNumber"])),
        ("Incorporated", "7 August 2024"),
        ("Registered office", esc(c["address"]["registeredOfficeFull"])),
        ("Classification", "UK SIC %s, %s" % (esc(c["industryClassification"]["code"]),
                                              esc(c["industryClassification"]["label"]))),
        ("Locations", esc(", ".join(c["locations"]))),
        ("Contact", '<a href="mailto:%s">%s</a>' % (esc(c["email"]), esc(c["email"]))),
        ("Certifications", esc(", ".join(x["name"] for x in d["certifications"]))),
    ]
    facts_html = ('<dl class="kp-facts">\n'
                  + "\n".join("<dt>%s</dt><dd>%s</dd>" % (k, v) for k, v in facts)
                  + "\n</dl>")

    cases = []
    for cs in d["caseStudies"]:
        label = cs["client"] or cs["clientLabel"]
        u = case_url(site, cs)
        cases.append(
            '<div class="kp-case">\n'
            '<h3><a href="%s">%s</a></h3>\n'
            '<p class="kp-case__meta">%s</p>\n'
            '<p>%s</p>\n</div>' % (esc(u), esc(label), esc(cs["sector"]), esc(cs["summary"])))
    cases_html = "\n".join(cases)

    faq_html = "\n".join(
        '<div class="kp-item"><h3>%s</h3><p>%s</p></div>' % (esc(f["q"]), esc(f["a"]))
        for f in d["faq"])

    def ul(items):
        return '<ul class="kp-list">' + "".join("<li>%s</li>" % esc(i) for i in items) + "</ul>"

    css = """
%s
:root {
%s
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: 'Switzer', system-ui, -apple-system, 'Segoe UI', sans-serif;
  font-weight: 400;
  font-size: clamp(15px, 1.05vw, 17px);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
.kp-wrap { max-width: 62rem; margin: 0 auto; padding: var(--space-xl) var(--gutter) var(--space-xl); }
a { color: var(--blue); text-underline-offset: .18em; }
a:hover { color: var(--signal); }
.kp-eyebrow {
  margin: 0 0 var(--space-xs);
  font-size: 11px; font-weight: 600; line-height: 1.2;
  letter-spacing: .11em; text-transform: uppercase; color: var(--blue);
}
h1 {
  font-family: 'Zodiak', Georgia, serif; font-weight: 400;
  font-size: clamp(2rem, 4.4vw, 3.4rem); line-height: 1.06;
  letter-spacing: -.02em; margin: 0 0 var(--space-s);
}
.kp-lede { font-size: clamp(1.05rem, 1.5vw, 1.32rem); line-height: 1.42; max-width: 46rem; margin: 0 0 var(--space-l); }
h2 {
  font-family: 'Zodiak', Georgia, serif; font-weight: 400;
  font-size: clamp(1.4rem, 2.3vw, 2rem); line-height: 1.14;
  letter-spacing: -.015em; margin: 0 0 var(--space-s);
}
h3 { font-size: 1rem; font-weight: 600; margin: 0 0 var(--space-2xs); line-height: 1.3; }
p { margin: 0 0 var(--space-xs); max-width: 46rem; }
.kp-section { padding-top: var(--space-l); border-top: 1px solid var(--line-dark); margin-top: var(--space-l); }
.kp-grid { display: grid; gap: var(--space-m); grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr)); }
.kp-item p, .kp-case p { max-width: none; }
.kp-list { margin: 0; padding: 0; list-style: none; display: flex; flex-wrap: wrap; gap: var(--space-2xs) var(--space-xs); }
.kp-list li { border: 1px solid var(--line-dark); border-radius: 999px; padding: .28em .82em; font-size: .92em; }
.kp-facts { display: grid; grid-template-columns: minmax(11rem, 16rem) 1fr; gap: var(--space-2xs) var(--space-m); margin: 0; }
.kp-facts dt { font-weight: 600; }
.kp-facts dd { margin: 0; }
.kp-case { padding-bottom: var(--space-s); border-bottom: 1px solid var(--line-dark); }
.kp-case:last-child { border-bottom: 0; padding-bottom: 0; }
.kp-case__meta { font-size: .82em; letter-spacing: .09em; text-transform: uppercase; color: var(--signal); margin: 0 0 var(--space-2xs); }
.kp-foot { margin-top: var(--space-l); padding-top: var(--space-s); border-top: 1px solid var(--line-dark); font-size: .88em; }
@media (max-width: 640px) { .kp-facts { grid-template-columns: 1fr; gap: var(--space-2xs); } .kp-facts dd { margin-bottom: var(--space-xs); } }
""" % ("\n".join(faces), tokens)

    return """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optia Data, company information</title>
<meta name="description" content="Structured company information for Optia Data: what it does, the data it works with, the industries it serves, and the published case studies behind each claim.">
<link rel="canonical" href="{page}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Optia Data">
<meta property="og:title" content="Optia Data, company information">
<meta property="og:description" content="What Optia Data does, the data it works with, the industries it serves, and the published case studies behind each claim.">
<meta property="og:url" content="{page}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Optia Data, company information">
<meta name="twitter:description" content="What Optia Data does, the data it works with, the industries it serves, and the published case studies behind each claim.">
<style>{css}</style>
<script type="application/ld+json">
{graph}
</script>
</head>
<body>
<main class="kp-wrap">

<p class="kp-eyebrow">Company information</p>
<h1>Optia Data</h1>
<p class="kp-lede">{lede}</p>

{overview}

{whatitdoes}

{services}

{expertise}

{industries}

{markets}

{sources}

{facts}

{cases}

{faq}

<p class="kp-foot">This page is a factual reference maintained for search engines, answer engines and anyone who needs Optia Data's details in one place. Last updated {updated}. Every claim on it is drawn from Optia Data's published case studies and company record. <a href="{origin}/">Optia Data home</a>.</p>

</main>
</body>
</html>
""".format(
        page=esc(page), css=css, graph=graph, updated=esc(d["lastUpdated"]), origin=esc(origin),
        lede=esc(c["description"]),
        overview=sec("Company overview",
                     "<p>Optia Data Ltd is a data and AI consultancy registered in England and Wales, company number %s, incorporated on 7 August 2024. It began as the services arm of a no-code data management platform and became a dedicated consultancy when clients kept asking for the data work rather than the software.</p>"
                     "<p>The company works from %s. Leadership sits in five countries across three continents, so client teams in different regions deal with someone in a comparable time zone.</p>"
                     % (esc(c["companyNumber"]), esc(", ".join(c["locations"]))), "overview"),
        whatitdoes=sec("What Optia Data does",
                       "<p>Commercial teams in consumer goods routinely hold several versions of the same number. Retailer EPOS says one thing, syndicated data says another, and internal systems say a third. Optia Data resolves those discrepancies before they reach category reporting, a board pack or a buyer meeting.</p>"
                       "<p>The work runs in three layers. Foundation puts the data in order. Context applies the client's own category definitions so figures can be compared without averaging across incompatible periods. Intelligence builds the reporting and analysis on top. AI is recommended where it fits and left out where it does not.</p>"
                       "<p>Every delivered output has a named analyst behind it who has checked the number.</p>", "what-optia-data-does"),
        services=sec("Services", '<div class="kp-grid">\n%s\n</div>' % services, "services"),
        expertise=sec("Areas of expertise", ul(d["expertise"]), "expertise"),
        industries=sec("Industries served",
                       "<p>Consumer goods and retail is where most published work sits. Optia Data also publishes engagements in financial services, education, engineering and health.</p>"
                       + ul(d["industries"]), "industries"),
        markets=sec("Markets and geographic coverage",
                    "<p>Published engagements cover up to 20 markets in a single reporting framework. "
                    "The markets below are those named in Optia Data's published case studies, as of %s.</p>" % d["asOf"]
                    + ul(d["markets"])
                    + "<h3>Optia Data locations</h3>"
                    + "<p>Where Optia Data itself works from, as distinct from the markets above.</p>"
                    + ul(c["locations"]), "markets"),
        sources=sec("Data sources, methodologies and technologies",
                    "<p>Optia Data works with syndicated market data, retailer data and clients' own systems, and harmonises them into one governed baseline. Processes run in a code-versioned and data-versioned setup with full lineage of every change, and are certified to ISO/IEC 27001:2022.</p>"
                    "<h3>Data sources</h3>" + ul(d["dataSources"]) +
                    "<h3>Methodologies</h3>" + ul(d["methodologies"]) +
                    "<h3>Technologies</h3>" + ul(d["technologies"]) +
                    "<h3>Partner network</h3>" + ul(d["partners"]), "data-sources"),
        facts=sec("Company facts", facts_html, "company-facts"),
        cases=sec("Clients and case studies",
                  "<p>Fifteen engagements are published in full. Fourteen name the client. One is a confidential financial services engagement published without a client name.</p>"
                  + cases_html, "case-studies"),
        faq=sec("Frequently asked questions", '<div class="kp-grid">\n%s\n</div>' % faq_html, "faq"),
    )


# --------------------------------------------------------------------------- #
#  llms.txt
# --------------------------------------------------------------------------- #
def build_llms(d):
    site, c = d["site"], d["company"]
    origin = site["origin"].rstrip("/")
    page = url_for(site, site["knowledgePagePath"])
    L = ["# Optia Data", "", "> " + c["description"], "",
         "Optia Data Ltd, registered in England and Wales, company number %s, incorporated 7 August 2024. "
         "Locations in %s. Data processes certified to ISO/IEC 27001:2022. "
         "Every delivered output has a named analyst behind it."
         % (c["companyNumber"], ", ".join(c["locations"])), "",
         "## About", "",
         "- [Company information](%s): full company record, services, expertise, industries, markets, data sources and case study index." % page,
         "- [Companies House record](https://find-and-update.company-information.service.gov.uk/company/%s): registered company details." % c["companyNumber"],
         "", "## Services", ""]
    for s in d["services"]:
        L.append("- **%s**: %s" % (s["name"], s["description"]))
    L += ["", "## Case studies", "",
          "Fifteen published engagements. Fourteen name the client; one financial services engagement is published without a client name.", ""]
    for cs in d["caseStudies"]:
        L.append("- [%s](%s): %s" % (cs["client"] or cs["clientLabel"], case_url(site, cs), cs["summary"]))
    L += ["", "## Insights", "",
          "- [Areas of expertise](%s#expertise): what Optia Data works on." % page,
          "- [Data sources, methodologies and technologies](%s#data-sources): the syndicated, retailer and internal data Optia Data harmonises, and the partner network behind it." % page,
          "- [Frequently asked questions](%s#faq): answers on data sources, industries, security certification, AI use and accountability." % page,
          "", "## Contact", "",
          "- Email: %s" % c["email"],
          "- Privacy enquiries: %s" % c["privacyEmail"],
          "- Registered office: %s" % c["address"]["registeredOfficeFull"],
          "", "Last updated %s." % d["lastUpdated"], ""]
    return "\n".join(L)


def main():
    d = json.loads(io.open(DATA, encoding="utf-8").read())
    faces, tokens = load_source_css()
    if len(faces) != len(WANT_FONTS):
        sys.exit("expected %d @font-face blocks, lifted %d" % (len(WANT_FONTS), len(faces)))

    out_page = os.path.join(V7, "company-data", "index.html")
    os.makedirs(os.path.dirname(out_page), exist_ok=True)
    io.open(out_page, "w", encoding="utf-8", newline="\n").write(build_page(d, faces, tokens))
    io.open(os.path.join(V7, "llms.txt"), "w", encoding="utf-8", newline="\n").write(build_llms(d))

    json.dumps(build_graph(d))  # fail loudly if the graph is not serialisable
    print("wrote v7/company-data/index.html  %d bytes" % os.path.getsize(out_page))
    print("wrote v7/llms.txt                 %d bytes" % os.path.getsize(os.path.join(V7, "llms.txt")))


if __name__ == "__main__":
    main()
