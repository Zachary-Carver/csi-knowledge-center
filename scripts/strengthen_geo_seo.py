#!/usr/bin/env python3
"""Strengthen Knowledge Center geographic SEO/GEO around CSI's real home market.

Primary hierarchy: Dallas-Fort Worth (DFW) Metroplex -> North Texas -> named local
service markets. Qualifying statewide Texas response remains secondary and is never
represented as separate offices.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "https://cleansceneinvestigators.com"
PORTFOLIO = "https://christina.cleansceneinvestigators.com"
REGION = "Dallas-Fort Worth (DFW) Metroplex"
REGION_SCHEMA = "Dallas-Fort Worth Metroplex, Texas"
NORTH_TEXAS = "North Texas"
PHONE = "940-654-6334"
LOGO = MAIN + "/assets/local/dce997b862bdca765a11.png"

GEO_BLOCK = re.compile(r"\n?<!-- CSI GEO SEO START -->.*?<!-- CSI GEO SEO END -->\n?", re.S)
GEO_SCHEMA = re.compile(r"\n?<!-- CSI GEO SCHEMA START -->.*?<!-- CSI GEO SCHEMA END -->\n?", re.S)

SERVICE_META = {
    "crime-scene-cleanup-dfw": ("Crime Scene Cleanup Dallas-Fort Worth | CSI Answers", "crime scene and trauma cleanup"),
    "biohazard-cleanup-dfw": ("Biohazard Cleanup Dallas-Fort Worth | CSI Answers", "biohazard and trauma cleanup"),
    "blood-cleanup": ("Blood Cleanup Dallas-Fort Worth | CSI Answers", "blood and bodily-fluid cleanup"),
    "unattended-death-cleanup": ("Unattended Death Cleanup Dallas-Fort Worth | CSI Answers", "unattended death cleanup"),
    "decomposition-cleanup": ("Decomposition Cleanup Dallas-Fort Worth | CSI Answers", "decomposition cleanup"),
    "hoarding-cleanup": ("Hoarding Cleanup Dallas-Fort Worth & North Texas | CSI Answers", "hazardous hoarding cleanup"),
    "odor-remediation": ("Forensic Odor Removal Dallas-Fort Worth | CSI Answers", "forensic odor remediation"),
    "vehicle-biohazard-cleanup": ("Vehicle Biohazard Cleanup Dallas-Fort Worth | CSI Answers", "vehicle biohazard cleanup"),
}

TOP_CITIES = ["Dallas", "Fort Worth", "Denton", "Plano", "Frisco", "Arlington", "Irving", "McKinney", "Keller", "Southlake", "Lewisville", "Flower Mound"]

META_OVERRIDES = {
    "answers/after-police-release-crime-scene/index.html": "After police release a scene, restrict access, identify the authorized decision-maker and contact a specialty cleanup provider serving DFW and North Texas.",
    "answers/biohazard-cleanup-denton/index.html": "24/7 crime scene, trauma, blood, unattended-death and biohazard cleanup in Denton, within the Dallas-Fort Worth (DFW) and North Texas service area.",
    "answers/bleach-blood-cleanup/index.html": "Learn why bleach alone may not safely address hidden or porous blood contamination and when professional cleanup is needed in DFW and North Texas.",
    "answers/blood-cleanup-denton/index.html": "Specialty blood and bodily-fluid cleanup in Denton, Texas and Denton County, within CSI's Dallas-Fort Worth and North Texas service area.",
    "answers/is-dried-blood-still-a-biohazard/index.html": "Dried blood may remain hazardous. Learn when affected surfaces need professional assessment and remediation across DFW and North Texas.",
    "answers/landlord-after-tenant-death/index.html": "After a tenant death, confirm scene release, restrict access and arrange specialty remediation with a DFW and North Texas cleanup provider.",
    "answers/unattended-death-cleanup-denton/index.html": "Unattended-death and decomposition cleanup in Denton and Denton County, within CSI's Dallas-Fort Worth and North Texas service area.",
    "answers/who-cleans-after-unattended-death/index.html": "After authorities release the property, a specialty biohazard company—not police or a funeral home—handles cleanup across DFW and North Texas.",
    "answers/who-cleans-blood-after-police-leave/index.html": "After police release a scene, owners or authorized representatives arrange professional blood cleanup across DFW and North Texas.",
    "answers/who-cleans-crime-scene-denton/index.html": "Who cleans a crime scene in Denton after police leave? CSI provides 24/7 specialty remediation across Dallas-Fort Worth and North Texas.",
    "answers/index.html": "Answers about crime scene, blood, biohazard, unattended-death, hoarding, vehicle and odor cleanup across Dallas-Fort Worth and North Texas.",
    "blog-media/index.html": "Official CSI educational content, media, podcast and social profiles supporting crime scene and biohazard cleanup authority across DFW and North Texas.",
    "crime-scene-cleanup-denton/index.html": "24/7 crime scene, trauma, blood and biohazard cleanup in Denton and Denton County, within Dallas-Fort Worth (DFW) and North Texas.",
    "official-business-information/index.html": "Official CSI identity, contact details and specialty cleanup scope for Dallas-Fort Worth and North Texas, with statewide Texas response secondary.",
    "service-areas/index.html": "CSI's primary service area is Dallas-Fort Worth (DFW) and North Texas, followed by named cities and qualifying statewide Texas response.",
    "services/index.html": "CSI crime scene, trauma, blood, unattended-death, hoarding, odor and vehicle biohazard cleanup across Dallas-Fort Worth and North Texas.",
    "site-architecture/index.html": "CSI authority map connecting the canonical website, specialty services, DFW and North Texas locations, answers and supporting content.",
    "women-in-power-christina-hester/index.html": "Christina Hester, former Crime Scene Investigator and CSI founder, is featured in Women in Power on Inside Success TV.",
}


def reconcile_schema(value):
    if isinstance(value, list):
        return [reconcile_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    for key, item in list(value.items()):
        value[key] = reconcile_schema(item)
    kind = value.get("@type")
    if isinstance(kind, list) and "LocalBusiness" in kind:
        value["@type"] = [item for item in kind if item != "LocalBusiness"]
        kind = value["@type"]
    elif kind == "LocalBusiness":
        value["@type"] = "Organization"
        kind = "Organization"
    kinds = kind if isinstance(kind, list) else [kind]
    if "Organization" in kinds:
        value["logo"] = {"@type": "ImageObject", "url": LOGO, "width": 180, "height": 180}
    return value


def reconcile_html_schema(source: str) -> str:
    pattern = re.compile(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.I | re.S)
    def replace(match: re.Match[str]) -> str:
        try:
            data = json.loads(html.unescape(match.group(2)))
        except (json.JSONDecodeError, TypeError):
            return match.group(0)
        data = reconcile_schema(data)
        return match.group(1) + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + match.group(3)
    return pattern.sub(replace, source)


def esc_attr(value: str) -> str:
    return html.escape(value, quote=True)


def set_title(source: str, value: str) -> str:
    tag = f"<title>{html.escape(value, quote=False)}</title>"
    if re.search(r"<title>.*?</title>", source, re.I | re.S):
        return re.sub(r"<title>.*?</title>", tag, source, count=1, flags=re.I | re.S)
    return source.replace("</head>", tag + "</head>", 1)


def set_meta(source: str, name: str, value: str) -> str:
    pattern = re.compile(rf"<meta\b(?=[^>]*\bname=[\"']{re.escape(name)}[\"'])[^>]*>", re.I)
    tag = f'<meta name="{esc_attr(name)}" content="{esc_attr(value)}">'
    if pattern.search(source):
        return pattern.sub(tag, source, count=1)
    return source.replace("</head>", tag + "</head>", 1)


def canonical(source: str) -> str:
    m = re.search(r"<link\b(?=[^>]*rel=[\"']canonical[\"'])[^>]*href=[\"']([^\"']+)", source, re.I)
    return html.unescape(m.group(1)) if m else ""


def city_from_path(path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    m = re.fullmatch(r"service-areas/([^/]+)/index\.html", rel)
    if not m:
        return None
    return " ".join(w.capitalize() for w in m.group(1).split("-"))


def regional_context(city: str | None = None) -> str:
    if city:
        lead = f"{city}, Texas is served within CSI's {REGION} and {NORTH_TEXAS} home market."
    else:
        lead = f"CSI's primary home market is the {REGION} and {NORTH_TEXAS}."
    cities = ", ".join(TOP_CITIES)
    return (
        f'<p><strong>{html.escape(lead)}</strong> CSI provides 24/7 specialty crime scene, trauma and biohazard cleanup across DFW, '
        f'including {html.escape(cities)} and surrounding communities. Qualifying statewide Texas response is available when logistics allow.</p>'
        f'<p><a href="{MAIN}/service-areas-in-texas/">Official Dallas-Fort Worth &amp; North Texas service areas</a> · '
        '<a href="/service-areas/">Knowledge Center city directory</a></p>'
    )


def inject_geo(source: str, url: str, city: str | None) -> str:
    source = GEO_BLOCK.sub("", source)
    source = GEO_SCHEMA.sub("", source)
    source = set_meta(source, "geo.region", "US-TX")
    source = set_meta(source, "geo.placename", f"{city}, Texas" if city else REGION_SCHEMA)

    coverage = []
    if city:
        coverage.append({"@type": "City", "name": f"{city}, Texas"})
    coverage += [{"@type": "Place", "name": REGION_SCHEMA}, {"@type": "Place", "name": NORTH_TEXAS}]
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": url + "#geographic-service-area",
        "url": url,
        "spatialCoverage": coverage,
        "about": {"@type": "Organization", "name": "CSI: Clean Scene Investigators", "url": MAIN + "/"},
    }
    schema_block = '\n<!-- CSI GEO SCHEMA START --><script type="application/ld+json" data-csi-geo-schema="true">' + json.dumps(schema, separators=(",", ":"), ensure_ascii=False) + '</script><!-- CSI GEO SCHEMA END -->\n'
    source = source.replace("</head>", schema_block + "</head>", 1)

    block = '\n<!-- CSI GEO SEO START --><div class="wrap csi-geo-seo" data-csi-geo-seo="true">' + regional_context(city) + '</div><!-- CSI GEO SEO END -->\n'
    if "</footer>" in source:
        source = source.replace("</footer>", block + "</footer>", 1)
    else:
        source = source.replace("</body>", block + "</body>", 1)
    return source


def update_html(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "404.html":
        return False
    source = path.read_text(encoding="utf-8")
    original = source

    source = source.replace("https://www.cleansceneinvestigators.com", MAIN)
    source = source.replace("https://christina-portfolio-site.vercel.app", PORTFOLIO)
    city = city_from_path(path)

    if rel == "index.html":
        title = "Dallas-Fort Worth Crime Scene Cleanup Answers | CSI Knowledge Center"
        desc = f"CSI answers about crime scene, trauma and biohazard cleanup across Dallas-Fort Worth (DFW) and {NORTH_TEXAS}, with statewide Texas response secondary."
        source = set_title(source, title)
        source = set_meta(source, "description", desc)
        source = source.replace("Texas crime scene, trauma and biohazard answers", "Dallas-Fort Worth (DFW) &amp; North Texas crime scene, trauma and biohazard answers")
        source = source.replace("<strong>Texas</strong>statewide service territory", "<strong>DFW</strong>primary metroplex home market")
        source = source.replace("Based in North Texas, available throughout Texas", "Dallas-Fort Worth and North Texas first, statewide Texas response available")
        source = source.replace("Denton, Denton County, DFW and North Texas are CSI's home market. Statewide response is available across Texas.", "The Dallas-Fort Worth (DFW) Metroplex and North Texas are CSI's primary home market, including Denton and Denton County. Qualifying statewide response is available across Texas.")
        source = source.replace("mobile specialty cleanup serving Texas.", "mobile specialty cleanup serving the Dallas-Fort Worth Metroplex and North Texas, with qualifying statewide Texas response.")
    elif rel == "service-areas/index.html":
        source = set_title(source, "Dallas-Fort Worth & North Texas Cleanup Service Areas | CSI")
        source = set_meta(source, "description", f"CSI's primary crime scene and biohazard service area is Dallas-Fort Worth (DFW) and {NORTH_TEXAS}, followed by named cities and statewide Texas response.")
        source = source.replace("CSI is a mobile specialty cleanup company serving Texas. Denton, Denton County, Dallas-Fort Worth and North Texas are the home market.", "CSI is a mobile specialty cleanup company whose primary home market is the Dallas-Fort Worth (DFW) Metroplex and North Texas, including Denton and Denton County.")
        source = source.replace("Exact canonical city pages", "Dallas-Fort Worth and North Texas local service markets")
    elif rel == "services/index.html":
        source = set_title(source, "Dallas-Fort Worth Crime Scene & Biohazard Services | CSI Answers")
        source = set_meta(source, "description", f"CSI crime scene, trauma, blood, unattended-death, hoarding, odor and vehicle biohazard cleanup across Dallas-Fort Worth and {NORTH_TEXAS}.")
    elif Path(rel).parent.name in SERVICE_META:
        title, service = SERVICE_META[Path(rel).parent.name]
        source = set_title(source, title)
        source = set_meta(source, "description", f"CSI provides 24/7 {service} across the {REGION} and {NORTH_TEXAS}, with qualifying statewide Texas response. Call {PHONE}.")
    elif city:
        source = set_meta(source, "description", f"24/7 crime scene, blood, unattended-death and biohazard cleanup in {city}, within Dallas-Fort Worth (DFW) and {NORTH_TEXAS}.")

    if rel in META_OVERRIDES:
        source = set_meta(source, "description", META_OVERRIDES[rel])

    url = canonical(source) or "https://answers.cleansceneinvestigators.com/"
    source = inject_geo(source, url, city)
    source = reconcile_html_schema(source)

    if source != original:
        path.write_text(source, encoding="utf-8")
        return True
    return False


def update_machine_files() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".json", ".jsonld", ".txt", ".md"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = text.replace("https://www.cleansceneinvestigators.com", MAIN).replace("https://christina-portfolio-site.vercel.app", PORTFOLIO)
        if path.suffix.lower() in {".json", ".jsonld"}:
            try:
                new = json.dumps(reconcile_schema(json.loads(new)), separators=(",", ":"), ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        if new != text:
            path.write_text(new, encoding="utf-8")

    business = ROOT / "business.jsonld"
    if business.exists():
        data = json.loads(business.read_text(encoding="utf-8"))
        data["url"] = MAIN + "/"
        data = reconcile_schema(data)
        data["description"] = f"Former Crime Scene Investigator-led mobile specialty cleanup company serving the {REGION} and {NORTH_TEXAS} for crime scene, trauma, biohazard, blood, homicide, suicide, unattended death, decomposition, hazardous hoarding, forensic odor and vehicle biohazard cleanup, with qualifying statewide Texas response."
        founder = data.get("founder", {})
        if isinstance(founder, dict):
            founder["@id"] = PORTFOLIO + "/#christina-hester"
            founder["url"] = PORTFOLIO + "/"
        existing = data.get("areaServed", [])
        city_items = [x for x in existing if isinstance(x, dict) and x.get("@type") == "City"]
        data["areaServed"] = [
            {"@type": "AdministrativeArea", "name": REGION_SCHEMA},
            {"@type": "AdministrativeArea", "name": NORTH_TEXAS},
            {"@type": "AdministrativeArea", "name": "Denton County, Texas"},
            {"@type": "State", "name": "Texas"},
            *city_items,
        ]
        business.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    locations = ROOT / "locations.json"
    if locations.exists():
        data = json.loads(locations.read_text(encoding="utf-8"))
        data["canonicalServiceAreaHub"] = MAIN + "/service-areas-in-texas/"
        data["primaryServiceRegion"] = REGION
        data["homeMarket"] = [REGION, NORTH_TEXAS, "Denton County", "Denton"]
        data["secondaryServiceTerritory"] = "Qualifying statewide Texas response"
        locations.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    llms = ROOT / "llms.txt"
    if llms.exists():
        text = llms.read_text(encoding="utf-8")
        marker = "## Geographic service hierarchy"
        block = (
            marker + "\n"
            f"Primary home market: {REGION} and {NORTH_TEXAS}.\n"
            "Core local markets include Dallas, Fort Worth, Denton, Plano, Frisco, Arlington, Irving, McKinney, Keller, Southlake, Lewisville and Flower Mound.\n"
            "Denton County is a primary local authority market. Qualifying statewide Texas response is secondary and does not imply separate offices or storefronts.\n"
        )
        if marker in text:
            text = re.sub(r"## Geographic service hierarchy.*?(?=\n## |\Z)", block.rstrip(), text, flags=re.S)
        else:
            text = text.rstrip() + "\n\n" + block
        llms.write_text(text, encoding="utf-8")


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*.html"):
        if ".git" in path.parts:
            continue
        changed += int(update_html(path))
    update_machine_files()
    print(f"Knowledge Center geographic SEO/GEO strengthened on {changed} HTML files plus machine-readable authority files.")


if __name__ == "__main__":
    main()
