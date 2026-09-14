#!/usr/bin/env python3
"""Repair known UTF-8 mojibake without altering URLs or site structure."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".txt", ".json", ".jsonld", ".md", ".py", ".js", ".css", ".xml", ".yml", ".yaml"}
REPLACEMENTS = {
    "\u00e2\u20ac\u2122": "\u2019",
    "\u00e2\u20ac\u0153": "\u201c",
    "\u00e2\u20ac\u009d": "\u201d",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u00a6": "\u2026",
    "\u00c2\u00b7": "\u00b7",
    "\u00f0\u0178\u0161\u00a8": "\U0001f6a8",
    "Dallas-Fort Worth (DFW) &amp; North Texas":
        "Dallas-Fort Worth (DFW) &amp; North Texas",
}


def main() -> None:
    changed = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        source = path.read_text(encoding="utf-8")
        repaired = source
        for bad, good in REPLACEMENTS.items():
            repaired = repaired.replace(bad, good)
        if repaired != source:
            path.write_text(repaired, encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())
    print(f"Repaired encoding in {len(changed)} files")
    for name in changed:
        print(name)


if __name__ == "__main__":
    main()
