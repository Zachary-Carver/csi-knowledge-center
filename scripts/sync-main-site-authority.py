#!/usr/bin/env python3
"""Generate CSI canonical-site authority artifacts from the live GoDaddy sitemap.

The August 26, 2026 audit established a 50-primary-page baseline. The commercial
site is allowed to grow. Every deployment now re-reads the live sitemap, keeps
GoDaddy blog/article and known system routes separate, records drift from the
checked-in baseline, and publishes the current exact canonical registry without
silently inventing or deleting URLs.
"""
from __future__ import annotations
import html, json, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT_SITEMAP = "https://www.cleansceneinvestigators.com/sitemap.xml"
ALLOWED_HOSTS = {"cleansceneinvestigators.com", "www.cleansceneinvestigators.com"}
BASELINE_PRIMARY_COUNT = 50
BASELINE_DATE = "2026-08-26"
NON_PRIMARY_PATHS = {
    "/home": "Duplicate GoDaddy home route; canonical home is /.",
    "/ols/products": "GoDaddy Online Store system/catalog route; not a designed CSI authority page.",
}
CONTENT_PREFIXES = {
    "/f/": "GoDaddy blog/article route; indexable supporting content, tracked separately from designed primary pages.",
}
REQUIRED_CANONICAL_PATHS = {
    "/", "/crime-scene-cleaning-dfw", "/biohazard-cleanup-in-dfw",
    "/unattended-death-cleanup", "/service-areas-in-texas", "/about-us", "/contact-us",
}
OUT_JSON = Path("canonical-main-site-pages.json")
OUT_TXT = Path("canonical-main-site-pages.txt")
OUT_HTML = Path("canonical-main-site-pages/index.html")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"CSI-Authority-Sync/2.0 (+https://answers.cleansceneinvestigators.com/)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def crawl_sitemap(url: str, seen: set[str], pages: list[str]) -> None:
    if url in seen: return
    seen.add(url)
    root = ET.fromstring(fetch(url))
    kind = local_name(root.tag)
    if kind == "sitemapindex":
        for node in root.iter():
            if local_name(node.tag) == "loc" and node.text:
                child = node.text.strip()
                if (urlparse(child).hostname or "").lower() in ALLOWED_HOSTS:
                    crawl_sitemap(child, seen, pages)
    elif kind == "urlset":
        for node in root.iter():
            if local_name(node.tag) == "loc" and node.text:
                page = node.text.strip()
                if (urlparse(page).hostname or "").lower() in ALLOWED_HOSTS:
                    pages.append(page)
    else:
        raise RuntimeError(f"Unsupported sitemap root element: {root.tag}")


def normalize(url: str) -> str:
    p = urlparse(url); path = p.path or "/"
    if path != "/" and path.endswith("/"): path = path[:-1]
    return "https://www.cleansceneinvestigators.com" + path + (f"?{p.query}" if p.query else "")


def page_label(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path: return "Home"
    return path.replace("%2F"," / ").replace("%26"," & ").replace("-"," ").title()


def reason_for(path: str) -> str | None:
    if path in NON_PRIMARY_PATHS: return NON_PRIMARY_PATHS[path]
    for prefix, reason in CONTENT_PREFIXES.items():
        if path.startswith(prefix): return reason
    return None


def render_list(urls: list[str]) -> str:
    return "".join(f'<li><a href="{html.escape(u)}">{html.escape(page_label(u))}</a><br><small>{html.escape(u)}</small></li>' for u in urls)


def read_previous() -> set[str]:
    if not OUT_JSON.exists(): return set()
    try:
        data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        return set(data.get("canonicalUrls", []))
    except Exception:
        return set()


def write_html(primary: list[str], observed: list[str], excluded: list[dict[str,str]], added: list[str], removed: list[str], generated_at: str) -> None:
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    schema = json.dumps({"@context":"https://schema.org","@type":"ItemList","@id":"https://answers.cleansceneinvestigators.com/canonical-main-site-pages/#list","name":"CSI current canonical main-site page registry","numberOfItems":len(primary),"itemListElement":[{"@type":"ListItem","position":i,"name":page_label(u),"url":u} for i,u in enumerate(primary,1)]},separators=(",",":"))
    excluded_html = "".join(f'<li><a href="{html.escape(x["url"])}">{html.escape(x["url"])}</a> — {html.escape(x["reason"])}</li>' for x in excluded) or "<li>None</li>"
    drift = f'<p><strong>Added since checked-in baseline:</strong> {len(added)} · <strong>Removed:</strong> {len(removed)}</p>'
    if added: drift += '<h3>New primary URLs detected</h3><ul>'+render_list(added)+'</ul>'
    if removed: drift += '<h3>Previously recorded URLs no longer observed</h3><ul>'+render_list(removed)+'</ul>'
    content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CSI Main Website Pages | Live Canonical Registry</title><meta name="description" content="Live-synchronized registry of CSI: Clean Scene Investigators main-site URLs from the canonical GoDaddy sitemap, with supporting blog and system routes identified separately."><meta name="robots" content="index,follow,max-snippet:-1"><link rel="canonical" href="https://answers.cleansceneinvestigators.com/canonical-main-site-pages/"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{schema}</script></head><body><header><div class="wrap nav"><a class="brand" href="/">CSI <span>KNOWLEDGE CENTER</span></a><nav><a href="/services/">Services</a><a href="/service-areas/">Cities</a><a href="/answers/">Questions</a><a href="/site-architecture/">Architecture</a></nav></div></header><main><section class="hero"><div class="wrap"><p class="eyebrow">Synchronized from the live canonical sitemap</p><h1>CSI's current main-site URL registry</h1><p class="lead">This page is regenerated during every Knowledge Center deployment from the live GoDaddy sitemap. The August 26 audit recorded a 50-primary-page baseline; legitimate additions are now recorded as site growth instead of causing deployment failure.</p><div class="answer"><strong>Current designed primary URLs: {len(primary)}</strong><br>All URLs observed in sitemap: {len(observed)}<br>Supporting blog/system routes tracked separately: {len(excluded)}<br>Historical audited primary baseline: {BASELINE_PRIMARY_COUNT} on {BASELINE_DATE}<br>Generated: {html.escape(generated_at)}</div></div></section><section class="light"><div class="wrap"><h2>Current canonical primary pages</h2><ol>{render_list(primary)}</ol></div></section><section><div class="wrap"><h2>Live sitemap drift and supporting content</h2>{drift}<h3>Blog and system routes kept outside the primary-page count</h3><ul>{excluded_html}</ul><p>Machine-readable versions: <a href="/canonical-main-site-pages.json">JSON</a> · <a href="/canonical-main-site-pages.txt">plain text</a>.</p></div></section></main><footer><div class="wrap"><strong>CSI: Clean Scene Investigators</strong> · 940-654-6334 · dfw.csi.info@gmail.com</div></footer></body></html>'''
    OUT_HTML.write_text(content, encoding="utf-8")


def main() -> int:
    previous = read_previous()
    pages: list[str] = []
    crawl_sitemap(ROOT_SITEMAP, set(), pages)
    observed = sorted(set(normalize(u) for u in pages), key=lambda u:(urlparse(u).path != "/", urlparse(u).path.lower(), u))
    excluded, primary = [], []
    for url in observed:
        reason = reason_for(urlparse(url).path)
        if reason: excluded.append({"url":url,"reason":reason})
        else: primary.append(url)
    paths = {urlparse(u).path for u in primary}
    missing_required = sorted(REQUIRED_CANONICAL_PATHS - paths)
    if len(primary) < 30:
        raise RuntimeError(f"Live sitemap returned only {len(primary)} primary URLs; refusing to publish a likely incomplete crawl.")
    if missing_required:
        raise RuntimeError(f"Required canonical CSI paths missing from live sitemap: {missing_required}")
    added = sorted(set(primary)-previous)
    removed = sorted(previous-set(primary))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {"name":"CSI live canonical main-site registry","source":ROOT_SITEMAP,"generatedAt":generated_at,"historicalAuditedBaseline":{"date":BASELINE_DATE,"primaryPageCount":BASELINE_PRIMARY_COUNT},"observedSitemapUrlCount":len(observed),"primaryPageCount":len(primary),"supportingContentAndSystemRouteCount":len(excluded),"canonicalUrls":primary,"observedSitemapUrls":observed,"excludedFromPrimaryArchitecture":excluded,"changeFromCheckedInBaseline":{"added":added,"removed":removed},"authorityRule":"Use canonicalUrls as the current live main-site registry. Supporting /f/ blog content and known GoDaddy system/duplicate routes remain crawlable authority but are tracked separately. Never invent city or service URLs."}
    OUT_JSON.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    OUT_TXT.write_text("# CSI current canonical main-site URLs\n# Source: "+ROOT_SITEMAP+f"\n# Current primary URLs: {len(primary)}; observed sitemap URLs: {len(observed)}; supporting/system: {len(excluded)}\n"+"\n".join(primary)+"\n",encoding="utf-8")
    write_html(primary,observed,excluded,added,removed,generated_at)
    print(json.dumps({"source":ROOT_SITEMAP,"observed":len(observed),"primary":len(primary),"supportingOrSystem":len(excluded),"addedSinceCheckedInBaseline":added,"removedSinceCheckedInBaseline":removed,"generatedAt":generated_at},indent=2))
    return 0

if __name__ == "__main__": sys.exit(main())
