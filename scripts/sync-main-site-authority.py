#!/usr/bin/env python3
"""Generate exact live CSI canonical-page authority artifacts from the GoDaddy sitemap."""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT_SITEMAP = "https://www.cleansceneinvestigators.com/sitemap.xml"
ALLOWED_HOSTS = {"cleansceneinvestigators.com", "www.cleansceneinvestigators.com"}
OUT_JSON = Path("canonical-main-site-pages.json")
OUT_TXT = Path("canonical-main-site-pages.txt")
OUT_HTML = Path("canonical-main-site-pages/index.html")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CSI-Authority-Sync/1.0 (+https://answers.cleansceneinvestigators.com/)"
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def crawl_sitemap(url: str, seen: set[str], pages: list[str]) -> None:
    if url in seen:
        return
    seen.add(url)
    root = ET.fromstring(fetch(url))
    kind = local_name(root.tag)
    if kind == "sitemapindex":
        for node in root.iter():
            if local_name(node.tag) == "loc" and node.text:
                child = node.text.strip()
                host = (urlparse(child).hostname or "").lower()
                if host in ALLOWED_HOSTS:
                    crawl_sitemap(child, seen, pages)
    elif kind == "urlset":
        for node in root.iter():
            if local_name(node.tag) == "loc" and node.text:
                page = node.text.strip()
                host = (urlparse(page).hostname or "").lower()
                if host in ALLOWED_HOSTS:
                    pages.append(page)
    else:
        raise RuntimeError(f"Unsupported sitemap root element: {root.tag}")


def normalize(url: str) -> str:
    parsed = urlparse(url)
    scheme = "https"
    host = "www.cleansceneinvestigators.com"
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return f"{scheme}://{host}{path}" + (f"?{parsed.query}" if parsed.query else "")


def page_label(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "Home"
    return path.replace("%2F", " / ").replace("%26", " & ").replace("-", " ").title()


def write_html(urls: list[str], generated_at: str) -> None:
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    items = "".join(
        f'<li><a href="{html.escape(url)}">{html.escape(page_label(url))}</a><br><small>{html.escape(url)}</small></li>'
        for url in urls
    )
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": "https://answers.cleansceneinvestigators.com/canonical-main-site-pages/#list",
            "name": "CSI canonical main-site page registry",
            "numberOfItems": len(urls),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": page_label(url),
                    "url": url,
                }
                for index, url in enumerate(urls, 1)
            ],
        },
        separators=(",", ":"),
    )
    content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CSI Canonical Main-Site Pages | Exact Live Registry</title><meta name="description" content="Exact live URL registry generated from the canonical CSI: Clean Scene Investigators GoDaddy sitemap."><meta name="robots" content="index,follow,max-snippet:-1"><link rel="canonical" href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages/"><link rel="stylesheet" href="https://answers.cleansceneinvestigators.com/assets/style.css"><script type="application/ld+json">{schema}</script></head><body><a class="skip" href="#main">Skip to content</a><header><div class="wrap nav"><a class="brand" href="https://answers.cleansceneinvestigators.com/">CSI <span>KNOWLEDGE CENTER</span></a><nav aria-label="Primary"><a href="https://answers.cleansceneinvestigators.com/site-architecture/">50-Page Architecture</a><a href="https://www.cleansceneinvestigators.com/">Official CSI Website</a><a href="https://www.cleansceneinvestigators.com/service-areas-in-texas">Service Areas</a></nav></div></header><main id="main"><section class="hero"><div class="wrap"><p class="eyebrow">Generated from the live canonical sitemap</p><h1>Exact CSI main-site page registry</h1><p class="lead">This page is generated at deployment from <strong>https://www.cleansceneinvestigators.com/sitemap.xml</strong>. It mirrors the actual canonical GoDaddy URLs rather than guessing page slugs.</p><div class="answer"><strong>Observed canonical URLs: {len(urls)}</strong><br>Generated: {html.escape(generated_at)}</div></div></section><section class="light"><div class="wrap"><h2>Canonical CSI pages</h2><ol>{items}</ol><p>Machine-readable versions: <a href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages.json">JSON</a> · <a href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages.txt">plain text</a>.</p><p>The commercial source of truth remains <a href="https://www.cleansceneinvestigators.com/">cleansceneinvestigators.com</a>.</p></div></section></main><footer><div class="wrap"><strong>CSI: Clean Scene Investigators</strong> · 940-654-6334 · dfw.csi.info@gmail.com</div></footer></body></html>'''
    OUT_HTML.write_text(content, encoding="utf-8")


def main() -> int:
    pages: list[str] = []
    crawl_sitemap(ROOT_SITEMAP, set(), pages)
    urls = sorted(set(normalize(url) for url in pages), key=lambda u: (urlparse(u).path != "/", urlparse(u).path.lower(), u))
    if len(urls) < 40:
        raise RuntimeError(f"Canonical sitemap returned only {len(urls)} URLs; refusing to publish an incomplete authority mirror")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "name": "CSI canonical main-site page registry",
        "source": ROOT_SITEMAP,
        "generatedAt": generated_at,
        "observedPageCount": len(urls),
        "expectedArchitectureAtLastAudit": {
            "auditedOn": "2026-08-25",
            "total": 50,
            "home": 1,
            "servicePages": 10,
            "resourcePages": 6,
            "serviceAreaPages": 27,
            "companyAboutPages": 4,
            "contactPages": 1,
            "privacyPages": 1,
        },
        "canonicalUrls": urls,
        "authorityRule": "These URLs are fetched from the live canonical CSI sitemap. Do not infer missing or alternate page slugs.",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_TXT.write_text("# CSI canonical main-site URLs\n# Source: " + ROOT_SITEMAP + "\n" + "\n".join(urls) + "\n", encoding="utf-8")
    write_html(urls, generated_at)
    print(json.dumps({"source": ROOT_SITEMAP, "observedPageCount": len(urls), "generatedAt": generated_at}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
