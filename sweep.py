"""Target-company careers-page sweeps: which companies to sweep today, and recording results.

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/sweep.py today
      Print today's sweep list: priority companies not swept in the last 2 days,
      then the companies swept longest ago, up to settings.json sweep_per_run (default 15).
      Shows each company's saved location-filtered URL and its notes heading in data/site-notes.md.
  PY tools/sweep.py done "<Company>" [filtered_url] [--found N]
      Record a finished sweep (date, filtered URL if given, how many jobs were on the list).
  PY tools/sweep.py failed "<Company>" "<what was tried>"
      Record a sweep that couldn't get to a filtered list for your area (shows in site notes; retried next rotation).
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "careers-pages.json"
NOTES = ROOT / "data" / "site-notes.md"
SETTINGS = ROOT / "settings.json"


def load():
    return json.loads(PAGES.read_text(encoding="utf-8"))


def save(pages):
    PAGES.write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8")


def days_since(d):
    if not d:
        return 9999
    return (date.today() - date.fromisoformat(d[:10])).days


def today():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    n = settings.get("sweep_per_run", 15)
    pages = load()
    prio = [p for p in pages if p.get("priority") and days_since(p.get("last_swept")) >= 2]
    rest = sorted([p for p in pages if p not in prio], key=lambda p: -days_since(p.get("last_swept")))
    picks = (prio + rest)[:n]
    notes = NOTES.read_text(encoding="utf-8") if NOTES.exists() else ""
    for p in picks:
        has_notes = f"## {p['company']}" in notes
        print(f"- {p['company']} | last swept: {p.get('last_swept') or 'never'} | "
              f"{'PRIORITY | ' if p.get('priority') else ''}"
              f"start at: {p.get('filtered_url') or p.get('url') or '(find careers page)'} | notes: {'yes' if has_notes else 'none yet'}")


def find(pages, company):
    for p in pages:
        if p["company"].lower() == company.lower():
            return p
    p = {"company": company, "url": None}
    pages.append(p)
    return p


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["today"]:
        today()
    elif args[:1] == ["done"] and len(args) >= 2:
        pages = load()
        p = find(pages, args[1])
        p["last_swept"] = date.today().isoformat()
        if len(args) >= 3 and not args[2].startswith("--"):
            p["filtered_url"] = args[2]
        if "--found" in args:
            p["last_found"] = int(args[args.index("--found") + 1])
        p.pop("last_failed", None)
        save(pages)
        print("recorded")
    elif args[:1] == ["failed"] and len(args) == 3:
        pages = load()
        p = find(pages, args[1])
        p["last_swept"] = date.today().isoformat()
        p["last_failed"] = f"{datetime.now():%Y-%m-%d}: {args[2]}"
        save(pages)
        print("recorded")
    else:
        sys.exit(__doc__)
