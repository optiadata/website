# -*- coding: utf-8 -*-
"""Render a social card per case study from the case study's own hero.

Every case study already opens on a full-bleed photograph carrying the client
logo, the sector, the headline and the standout number, set in the site's own
typeface. That is a better social card than anything composed separately, and
it cannot drift from the page it represents: change the headline and the card
changes with it on the next build.

So rather than compositing images by hand, the built page is opened at exactly
1200x630 and photographed. Only the furniture that means nothing outside the
site is hidden first: the navigation, the back link and the cookie banner.

Depends on tools/build-routes.py having run, since it reads the built pages.

Usage:  python tools/build-og-cards.py
"""
import io
import os
import re
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V7 = os.path.join(ROOT, "v7")
OUT = os.path.join(V7, "images", "og")
W, H = 1200, 630

# Hidden for the photograph only. Each is site furniture that would read as
# clutter in a LinkedIn feed, or in the banner's case would cover the image.
#
# The hero is also pinned to the full card height. Left to itself it stops
# short of 630px and the frame catches the top of the statistics strip below,
# which lands in the feed as a band of half-cut words on white.
HIDE = """
  .site-nav, #siteNav, .case-hero__top, #cookie-banner, .cc-banner,
  .intro, #intro { display: none !important; }
  .case-page.is-active .case-study__inner { display: none !important; }
  .case-page.is-active .case-hero {
    height: %dpx !important; min-height: %dpx !important;
  }
  html, body { overflow: hidden !important; background: #05070d !important; }
""" % (H, H)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def routes_with_cards():
    """Read the route table back out of the build script, so this cannot fall
    out of step with what was actually built."""
    src = io.open(os.path.join(ROOT, "tools", "build-routes.py"), encoding="utf-8").read()
    table = src[src.index("ROUTES = ["):src.index("]", src.index("ROUTES = ["))]
    out = []
    for path, _sid in re.findall(r'\("(/[a-z0-9/-]*/)",\s*"([a-z0-9-]+)"\)', table):
        if not path.startswith("/case-studies/") or path == "/case-studies/":
            continue
        built = os.path.join(V7, path.strip("/").replace("/", os.sep), "index.html")
        if not os.path.exists(built):
            raise SystemExit("not built yet, run tools/build-routes.py first: %s" % path)
        # A page whose og:image is the generic card has no hero of its own.
        # The confidential engagement is the one such case, and it must not
        # borrow another client's photograph.
        if "/images/og/" not in io.open(built, encoding="utf-8").read():
            print("  skipping %s, no hero image of its own" % path)
            continue
        out.append((path, path.strip("/").split("/")[-1]))
    return out


os.path.isdir(OUT) or os.makedirs(OUT)
targets = routes_with_cards()
port = free_port()
server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                          cwd=V7, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)

    base = "http://127.0.0.1:%d" % port
    print("rendering %d cards at %dx%d\n" % (len(targets), W, H))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": W, "height": H},
                                  device_scale_factor=1)
        page = ctx.new_page()
        for path, slug in targets:
            page.goto(base + path, wait_until="load", timeout=45000)
            page.add_style_tag(content=HIDE)
            # The hero photograph is the whole card, so waiting for the page's
            # load event is not enough: decode has to have finished or the
            # screenshot catches an empty frame.
            page.wait_for_function(
                """() => { const i = document.querySelector('.case-page.is-active .case-hero__img');
                           return !i || (i.complete && i.naturalWidth > 0); }""",
                timeout=20000)
            page.wait_for_timeout(250)
            dst = os.path.join(OUT, slug + ".jpg")
            page.screenshot(path=dst, type="jpeg", quality=86,
                            clip={"x": 0, "y": 0, "width": W, "height": H})
            print("  %-40s %6.0fKB" % ("/images/og/%s.jpg" % slug,
                                       os.path.getsize(dst) / 1024))
        browser.close()
finally:
    server.terminate()

total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("\n%d cards, %.1fMB total" % (len(os.listdir(OUT)), total / 1048576))
