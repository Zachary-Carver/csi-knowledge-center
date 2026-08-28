#!/usr/bin/env python3
"""Generate exact CSI primary-site authority artifacts from the live GoDaddy sitemap.

The live sitemap contains the designed 50-page primary information architecture plus
GoDaddy blog/article and system routes. Preserve every observed URL for discovery and
transparency, while keeping the designed 50-page architecture distinct for authority
and local-search purposes.
"""

from __future__ import annotations

import html
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT_SITEMAP = "https://www.cleansceneinvestigators.com/sitemap.xml"
ALLOWED_HOSTS = {"cleansceneinvestigators.com", "www.cleansceneinvestigators.com"}
EXPECTED_PRIMARY_COUNT = 50
NON_PRIMARY_PATHS = {
    "/home": "Duplicate GoDaddy home route; the canonical designed home is the root URL /.",
    "/ols/products": "GoDaddy Online Store system/catalog route; not part of CSI's designed 50-page primary information architecture.",
}
CONTENT_PREFIXES = {
    "/f/": "GoDaddy blog/article route; valuable indexable supporting content, but not one of CSI's fixed 50 designed primary pages.",
}
OUT_JSON = Path("canonical-main-site-pages.json")
OUT_TXT = Path("canonical-main-site-pages.txt")
OUT_HTML = Path("canonical-main-site-pages/index.html")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CSI-Authority-Sync/1.2 (+https://answers.cleansceneinvestigators.com/)"},
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
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return "https://www.cleansceneinvestigators.com" + path + (f"?{parsed.query}" if parsed.query else "")


def page_label(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "Home"
    return path.replace("%2F", " / ").replace("%26", " & ").replace("-", " ").title()


def render_items(urls: list[str]) -> str:
    return "".join(
        f'<li><a href="{html.escape(url)}">{html.escape(page_label(url))}</a><br><small>{html.escape(url)}</small></li>'
        for url in urls
    )


def non_primary_reason(path: str) -> str | None:
    reason = NON_PRIMARY_PATHS.get(path)
    if reason:
        return reason
    for prefix, prefix_reason in CONTENT_PREFIXES.items():
        if path.startswith(prefix):
            return prefix_reason
    return None


def write_html(primary_urls: list[str], observed_urls: list[str], excluded: list[dict[str, str]], generated_at: str) -> None:
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    primary_items = render_items(primary_urls)
    excluded_items = "".join(
        f'<li><a href="{html.escape(item["url"])}">{html.escape(item["url"])}</a> — {html.escape(item["reason"])}</li>'
        for item in excluded
    )
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": "https://answers.cleansceneinvestigators.com/canonical-main-site-pages/#list",
            "name": "CSI designed 50-page primary website registry",
            "numberOfItems": len(primary_urls),
            "itemListElement": [
                {"@type": "ListItem", "position": index, "name": page_label(url), "url": url}
                for index, url in enumerate(primary_urls, 1)
            ],
        },
        separators=(",", ":"),
    )
    content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CSI 50 Primary Website Pages | Exact Live Registry</title><meta name="description" content="Exact registry of CSI: Clean Scene Investigators' designed 50 primary website pages, synchronized from the live GoDaddy sitemap while preserving supporting blog and system URLs separately."><meta name="robots" content="index,follow,max-snippet:-1"><link rel="canonical" href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages/"><link rel="stylesheet" href="https://answers.cleansceneinvestigators.com/assets/style.css"><script type="application/ld+json">{schema}</script></head><body><a class="skip" href="#main">Skip to content</a><header><div class="wrap nav"><a class="brand" href="https://answers.cleansceneinvestigators.com/">CSI <span>KNOWLEDGE CENTER</span></a><nav aria-label="Primary"><a href="https://answers.cleansceneinvestigators.com/site-architecture/">50-Page Architecture</a><a href="https://www.cleansceneinvestigators.com/">Official CSI Website</a><a href="https://www.cleansceneinvestigators.com/service-areas-in-texas">Service Areas</a></nav></div></header><main id="main"><section class="hero"><div class="wrap"><p class="eyebrow">Synchronized from the live canonical sitemap</p><h1>CSI's exact designed 50-page primary website registry</h1><p class="lead">This registry is regenerated at deployment from <strong>https://www.cleansceneinvestigators.com/sitemap.xml</strong>. It preserves the actual live slugs for CSI's designed primary pages instead of guessing local URLs, while retaining blog/article URLs as supporting authority content.</p><div class="answer"><strong>Designed primary pages: {len(primary_urls)}</strong><br>URLs currently observed in sitemap: {len(observed_urls)}<br>Supporting content/system routes: {len(excluded)}<br>Generated: {html.escape(generated_at)}</div></div></section><section class="light"><div class="wrap"><h2>The 50 primary CSI pages</h2><ol>{primary_items}</ol><p>Machine-readable versions: <a href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages.json">JSON</a> · <a href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages.txt">plain text</a>.</p></div></section><section><div class="wrap"><h2>Additional sitemap content outside the fixed 50-page architecture</h2><p>These live URLs remain part of CSI's crawlable authority surface, but they are not counted as one of the fixed 50 designed primary pages:</p><ul>{excluded_items}</ul><p>The commercial source of truth remains <a href="https://www.cleansceneinvestigators.com/">cleansceneinvestigators.com</a>.</p></div></section></main><footer><div class="wrap"><strong>CSI: Clean Scene Investigators</strong> · 940-654-6334 · dfw.csi.info@gmail.com</div></footer></body></html>'''
    OUT_HTML.write_text(content, encoding="utf-8")


def main() -> int:
    pages: list[str] = []
    crawl_sitemap(ROOT_SITEMAP, set(), pages)
    observed_urls = sorted(set(normalize(url) for url in pages), key=lambda u: (urlparse(u).path != "/", urlparse(u).path.lower(), u))

    excluded: list[dict[str, str]] = []
    primary_urls: list[str] = []
    for url in observed_urls:
        path = urlparse(url).path
        reason = non_primary_reason(path)
        if reason:
            excluded.append({"url": url, "reason": reason})
        else:
            primary_urls.append(url)

    if len(primary_urls) != EXPECTED_PRIMARY_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_PRIMARY_COUNT} designed primary URLs after separating blog/system content, found {len(primary_urls)} "
            f"from {len(observed_urls)} sitemap URLs. Review architecture before publishing."
        )

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "name": "CSI designed primary-site page registry",
        "source": ROOT_SITEMAP,
        "generatedAt": generated_at,
        "observedSitemapUrlCount": len(observed_urls),
        "primaryPageCount": len(primary_urls),
        "expectedPrimaryPageCount": EXPECTED_PRIMARY_COUNT,
        "supportingContentAndSystemRouteCount": len(excluded),
        "architecture": {
            "home": 1,
            "servicePages": 10,
            "resourcePages": 6,
            "serviceAreaPages": 27,
            "companyAboutPages": 4,
            "contactPages": 1,
            "privacyPages": 1,
            "total": 50,
        },
        "canonicalUrls": primary_urls,
        "observedSitemapUrls": observed_urls,
        "excludedFromPrimaryArchitecture": excluded,
        "authorityRule": "Use canonicalUrls for CSI's fixed 50-page designed primary authority architecture. observedSitemapUrls preserves every live sitemap URL, including supporting GoDaddy blog/article content and explicitly identified system routes.",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_TXT.write_text(
        "# CSI designed 50-page primary website URLs\n"
        f"# Source: {ROOT_SITEMAP}\n"
        f"# Observed sitemap URLs: {len(observed_urls)}; primary authority pages: {len(primary_urls)}; supporting content/system routes: {len(excluded)}\n"
        + "\n".join(primary_urls)
        + "\n",
        encoding="utf-8",
    )
    write_html(primary_urls, observed_urls, excluded, generated_at)
    print(json.dumps({
        "source": ROOT_SITEMAP,
        "observedSitemapUrlCount": len(observed_urls),
        "primaryPageCount": len(primary_urls),
        "supportingContentAndSystemRouteCount": len(excluded),
        "excludedFromPrimaryArchitecture": excluded,
        "generatedAt": generated_at,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
