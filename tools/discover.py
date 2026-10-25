"""Company discovery: an open-ended search for new employers, plus a company memory.

Instead of checking the same fixed list of companies every day, each run uses a different mix of
"lenses" (ways of finding companies), so the search never repeats itself. Every company found is
remembered in data/companies.json, so it is never investigated twice for nothing.

What it searches for comes from settings.json (setup fills these from me/search-criteria):
  discovery_roles    job titles to search for, e.g. ["business analyst", "graduate program"]
  discovery_places   cities/areas to search in (default: home_country)
  discovery_sectors  industries for the "sector leaders" lens

Commands (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/discover.py plan [--place "<City>"]
        Today's searches (lens, query, domains) + companies due a re-check.
        --place = a location the user named for this run ("morning run for <City>"); default = their area.
  PY tools/discover.py known "<Company>"
        Is this company already in the memory? Prints its record.
  PY tools/discover.py add <file.json>
        Add/update companies: [{name, type, found_via, why, careers_url, system, jobs_url, feed, verdict, notes}]
  PY tools/discover.py checked "<Company>" --verdict watch|skip [--found N] [--note "..."] [--place "<City>"]
        Record that a company was investigated today (with --place, kept separate per location).
  PY tools/discover.py new-today
        Companies first found today (for the morning summary).
  PY tools/discover.py seed
        Import data/careers-pages.json + data/feeds.json into the memory (setup, or once after updating).

type: multinational | top_local | startup | other
verdict: watch (good employer for the user: re-check after discovery_recheck_days or when it shows up again)
         skip (not useful: nothing fitting / no roles in the area / no way to apply on its own site)
         new (not investigated yet)
"""
import json
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import DATA, ME, settings  # noqa: E402

MEM = DATA / "companies.json"
PAST = ME / "target-companies" / "past-applications.md"

DEFAULT_ROLES = ["business analyst", "operations analyst", "project coordinator", "graduate program",
                 "management trainee", "account manager", "customer success", "marketing specialist"]
DEFAULT_SECTORS = ["FMCG", "fintech", "e-commerce", "logistics", "energy", "pharma", "consulting", "real estate",
                   "banking", "telecom", "software and SaaS", "automotive", "healthcare", "manufacturing",
                   "renewable energy", "education technology", "travel", "insurance", "market research", "retail"]
ATS = [["boards.greenhouse.io", "job-boards.greenhouse.io"], ["jobs.lever.co"], ["jobs.ashbyhq.com"],
       ["apply.workable.com"], ["myworkdayjobs.com"], ["jobs.smartrecruiters.com"], ["teamtailor.com"],
       ["successfactors.com", "successfactors.eu"], ["breezy.hr", "bamboohr.com", "recruitee.com"]]


def cfg():
    s = settings()
    places = s.get("discovery_places") or ([s["home_country"]] if s.get("home_country") else [])
    return {
        "roles": s.get("discovery_roles") or DEFAULT_ROLES,
        "places": places,
        "region": s.get("home_country") or (places[0] if places else ""),
        "sectors": s.get("discovery_sectors") or DEFAULT_SECTORS,
        "blocked": s.get("blocked_sites", []),
        "searches": int(s.get("discovery_searches_per_run", 4)),
        "rechecks": int(s.get("discovery_rechecks_per_run", 3)),
        "recheck_days": int(s.get("discovery_recheck_days", 30)),
    }


def lenses(d, where=None):
    """Every lens, each giving one search for day d (rotates with the date).
    where = a location the user named for this run; None = their normal area (settings)."""
    c = cfg()
    n = d.toordinal()
    rng = random.Random(n)
    roles, sectors = c["roles"], c["sectors"]
    places = [where] if where else (c["places"] or [""])
    area = where or c["region"]
    month = d.strftime("%B %Y")
    sector = sectors[n % len(sectors)]
    blocked = c["blocked"]
    out = {
        "ats": {"why": "Job-system search: finds companies you've never heard of",
                "query": f"{roles[n % len(roles)]} {places[n % len(places)]}".strip(),
                "allowed_domains": ATS[n % len(ATS)]},
        "ats2": {"why": "Second job-system search, different system and role",
                 "query": f"{roles[(n * 7 + 3) % len(roles)]} {places[(n + 1) % len(places)]}".strip(),
                 "allowed_domains": ATS[(n * 5 + 2) % len(ATS)]},
        "startups": {"why": "Exciting start-ups: recent funding usually means hiring",
                     "query": rng.choice([f"{area} startup raises funding {month}", f"{area} startup series A {d.year}",
                                          f"{area} startup seed round {month}", f"{area} startups hiring {d.year}"]),
                     "blocked_domains": blocked},
        "hubs": {"why": f"Multinationals opening or growing offices in {area}",
                 "query": rng.choice([f"multinational opens {area} office {d.year}",
                                      f"global company expands {area} office {d.year}",
                                      f"shared services centre {area} {d.year}",
                                      f"regional headquarters {area} {d.year}"]),
                 "blocked_domains": blocked},
        "sector": {"why": f"Biggest and fastest-growing {sector} companies in {area}",
                   "query": rng.choice([f"largest {sector} companies in {area}",
                                        f"fastest growing {sector} companies {area} {d.year}",
                                        f"top {sector} employers {area}"]),
                   "blocked_domains": blocked},
        "programmes": {"why": "Graduate, rotational and trainee programmes open now",
                       "query": rng.choice([f"graduate program {area} {d.year} apply",
                                            f"management trainee program {area} {d.year}",
                                            f"rotational graduate programme {area} {d.year}"]),
                       "blocked_domains": blocked},
    }
    past = past_companies()
    if past:
        look = past[n % len(past)]
        out["lookalike"] = {"why": f"Companies similar to {look} (from your applications)",
                            "query": f"companies similar to {look} in {area}", "blocked_domains": blocked}
    return out


def pick(d, where=None):
    """A job-system search every day (the main source) + a different mix of the other lenses each day."""
    L = lenses(d, where)
    others = [k for k in L if k != "ats"]
    rng = random.Random(d.toordinal() * 31)
    chosen = ["ats"] + rng.sample(others, max(0, min(len(others), cfg()["searches"] - 1)))
    out = []
    for k in chosen:
        s = dict(L[k], query=" ".join(L[k]["query"].split()))  # tidy spaces when no place is set
        out.append((k, s))
    return out


def past_companies():
    """Company column of the table rows in past-applications.md (rows start with a date)."""
    if not PAST.exists():
        return []
    out = []
    for line in PAST.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0][:4].isdigit() and cells[1] and cells[1] not in out:
            out.append(cells[1])
    return out


def load():
    try:
        return json.loads(MEM.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(mem):
    MEM.parent.mkdir(exist_ok=True)
    MEM.write_text(json.dumps(sorted(mem, key=lambda c: c["name"].lower()), indent=1, ensure_ascii=False),
                   encoding="utf-8")


def norm(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def find(mem, name):
    k = norm(name)
    for c in mem:
        if norm(c["name"]) == k or k in [norm(a) for a in c.get("aliases", [])]:
            return c
    return None


def days_since(s):
    try:
        return (date.today() - date.fromisoformat(s[:10])).days
    except (TypeError, ValueError):
        return 9999


def at(c, where):
    """A company's verdict / last check for this run's location (normal area = the top-level fields)."""
    return c.get("by_place", {}).get(where, {}) if where else c


def plan(where=None):
    c = cfg()
    d = date.today()
    if not where and not c["places"]:
        print("Note: settings.json has no discovery_places or home_country yet; searches won't name a place.")
    print(f"Discovery plan for {d}{' in ' + where if where else ''} (run each search with WebSearch):")
    for i, (k, s) in enumerate(pick(d, where), 1):
        dom = (f"allowed_domains={s['allowed_domains']}" if "allowed_domains" in s
               else f"blocked_domains={s['blocked_domains']}")
        print(f"  {i}. [{k}] {s['why']}\n     query: {s['query']}\n     {dom}")
    mem = load()
    due = [m for m in mem if at(m, where).get("verdict") == "watch" and not m.get("feed")  # feeds: checked every run
           and days_since(at(m, where).get("last_checked", "")) >= c["recheck_days"]]
    due.sort(key=lambda m: at(m, where).get("last_checked", ""))
    print(f"\nCompanies due a re-check (watch, {c['recheck_days']}+ days, max {c['rechecks']}):")
    for m in due[:c["rechecks"]]:
        last = at(m, where).get("last_checked") or "never"
        print(f"  - {m['name']} (last {last}): {m.get('jobs_url') or m.get('careers_url') or 'no URL yet'}")
    if not due:
        print("  (none)")
    print(f"\nMemory: {len(mem)} companies ({sum(m.get('verdict') == 'watch' for m in mem)} watch, "
          f"{sum(m.get('verdict') == 'skip' for m in mem)} skip, "
          f"{sum(m.get('verdict') == 'new' for m in mem)} not yet investigated)")


def add(path):
    mem = load()
    today = str(date.today())
    added, updated = [], []
    for rec in json.loads(Path(path).read_text(encoding="utf-8-sig")):
        c = find(mem, rec["name"])
        if c:
            for k, v in rec.items():
                if v not in (None, "", []):
                    c[k] = v
            c.setdefault("history", []).append(f"{today}: updated ({rec.get('found_via', 'run')})")
            updated.append(c["name"])
        else:
            rec.setdefault("verdict", "new")
            rec.update(first_seen=today, last_checked=rec.get("last_checked", ""))
            rec.setdefault("history", []).append(f"{today}: found via {rec.get('found_via', '?')}")
            mem.append(rec)
            added.append(rec["name"])
    save(mem)
    print(f"Added {len(added)}: {', '.join(added) or '-'}")
    print(f"Updated {len(updated)}: {', '.join(updated) or '-'}")


def opt(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default


def checked(name, args):
    mem = load()
    c = find(mem, name)
    if not c:
        print(f"Not in memory: {name}. Add it first (discover.py add).")
        return
    verdict = opt(args, "--verdict", c.get("verdict", "new"))
    found = int(opt(args, "--found", 0))
    note = opt(args, "--note", "")
    where = opt(args, "--place")
    today = str(date.today())
    if where:  # a location the user named: keep its verdict separate from their normal area
        c.setdefault("by_place", {})[where] = {"verdict": verdict, "last_checked": today, "last_found": found}
    else:
        c.update(verdict=verdict, last_checked=today, last_found=found)
    c.setdefault("history", []).append(f"{today}: checked{' (' + where + ')' if where else ''}, {found} fitting, "
                                       f"verdict {verdict}{'. ' + note if note else ''}")
    save(mem)
    print(f"{c['name']}: {verdict}, {found} fitting")


def new_today():
    today = str(date.today())
    rows = [c for c in load() if c.get("first_seen") == today]
    for c in rows:
        print(f"- {c['name']} ({c.get('type') or '?'}): {c.get('why', '')} [{c.get('verdict')}]")
    if not rows:
        print("(no new companies today)")


def seed():
    mem = load()
    today = str(date.today())
    n = 0
    pages_file, feeds_file = DATA / "careers-pages.json", DATA / "feeds.json"
    pages = json.loads(pages_file.read_text(encoding="utf-8")) if pages_file.exists() else []
    feeds = json.loads(feeds_file.read_text(encoding="utf-8")) if feeds_file.exists() else []
    for p in pages:
        if p.get("company") and not find(mem, p["company"]):
            mem.append({"name": p["company"], "type": "", "found_via": "target list", "why": "On your target list",
                        "careers_url": p.get("url", ""), "jobs_url": p.get("filtered_url") or p.get("manual_url", ""),
                        "verdict": "watch", "target": True, "first_seen": today,
                        "last_checked": p.get("last_swept", ""), "last_found": p.get("last_found", 0),
                        "notes": p.get("note", ""), "history": [f"{today}: imported from careers-pages.json"]})
            n += 1
    for f in feeds:
        if not f.get("company"):
            continue
        c = find(mem, f["company"])
        if c:
            c["feed"] = f"{f['ats']}:{f['token']}"
        else:
            mem.append({"name": f["company"], "type": "", "found_via": "job feed",
                        "why": "Public job feed, checked every run", "feed": f"{f['ats']}:{f['token']}",
                        "verdict": "watch", "first_seen": today, "last_checked": "",
                        "history": [f"{today}: imported from feeds.json"]})
            n += 1
    save(mem)
    print(f"Seeded {n}; memory now {len(mem)} companies")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "plan":
        plan(opt(a, "--place"))
    elif a[0] == "known" and len(a) > 1:
        c = find(load(), a[1])
        print(json.dumps(c, indent=1, ensure_ascii=False) if c else "unknown")
    elif a[0] == "add" and len(a) > 1:
        add(a[1])
    elif a[0] == "checked" and len(a) > 1:
        checked(a[1], a[2:])
    elif a[0] == "new-today":
        new_today()
    elif a[0] == "seed":
        seed()
    else:
        print(__doc__)
