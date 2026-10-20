"""Check public job feeds (Greenhouse, Lever, Ashby, SmartRecruiters, Workable).

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/feeds.py discover "Company A" "Company B" ...
      Probe each company on every feed type; save the ones that answer to data/feeds.json.
  PY tools/feeds.py scan
      Fetch every feed in data/feeds.json, keep postings whose location matches
      settings.json "location_keywords", skip ones already seen or already in jobs/,
      and write the new ones to data/candidates.json for Claude to score.

Only public, no-login job APIs are used. Sites in settings.json "blocked_sites" are never contacted.
"""
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import blocked  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FEEDS = ROOT / "data" / "feeds.json"
CANDIDATES = ROOT / "data" / "candidates.json"
SEEN = ROOT / "data" / "seen.json"
SETTINGS = ROOT / "settings.json"


def get_json(url, timeout=20):
    if blocked(url):
        raise ValueError("Blocked site")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (personal job search)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def strip_html(text):
    text = html.unescape(text or "")
    text = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ---------- one reader per feed type: each returns a list of uniform postings ----------

def greenhouse(token):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    return [{"title": j["title"], "location": (j.get("location") or {}).get("name", ""),
             "apply_url": j["absolute_url"], "posting_text": strip_html(j.get("content", "")),
             "posted": j.get("updated_at", "")[:10]} for j in data.get("jobs", [])]


def lever(token):
    data = get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    out = []
    for j in data:
        cats = j.get("categories", {})
        lists = "\n".join(f"{l.get('text','')}\n{strip_html(l.get('content',''))}" for l in j.get("lists", []))
        out.append({"title": j["text"], "location": cats.get("location", "") or ", ".join(cats.get("allLocations", [])),
                    "employment_type": cats.get("commitment", ""), "apply_url": j.get("hostedUrl", ""),
                    "posting_text": (j.get("descriptionPlain", "") + "\n\n" + lists).strip(), "posted": ""})
    return out


def ashby(token):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
    return [{"title": j["title"], "location": j.get("location", "") + (" (remote)" if j.get("isRemote") else ""),
             "employment_type": j.get("employmentType", ""), "apply_url": j.get("jobUrl", ""),
             "posting_text": j.get("descriptionPlain", ""), "posted": (j.get("publishedAt") or "")[:10]}
            for j in data.get("jobs", [])]


def smartrecruiters(token):
    data = get_json(f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100")
    out = []
    for j in data.get("content", []):
        loc = j.get("location", {})
        out.append({"title": j["name"], "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x)
                    + (" (remote)" if loc.get("remote") else ""),
                    "apply_url": f"https://jobs.smartrecruiters.com/{token}/{j['id']}", "posting_text": "",
                    "detail_api": f"https://api.smartrecruiters.com/v1/companies/{token}/postings/{j['id']}",
                    "posted": (j.get("releasedDate") or "")[:10]})
    return out


def workable(token):
    data = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=true")
    return [{"title": j["title"], "location": ", ".join(x for x in [j.get("city"), j.get("country")] if x)
             + (" (remote)" if j.get("telecommuting") else ""),
             "employment_type": j.get("employment_type", ""), "apply_url": j.get("url") or j.get("shortlink", ""),
             "posting_text": strip_html(j.get("description", "")), "posted": j.get("published_on", "")}
            for j in data.get("jobs", [])]


READERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby,
           "smartrecruiters": smartrecruiters, "workable": workable}


def smartrecruiters_detail(p):
    """SmartRecruiters lists postings without text; fetch it for the ones we keep."""
    try:
        d = get_json(p["detail_api"])
        secs = d.get("jobAd", {}).get("sections", {})
        p["posting_text"] = "\n\n".join(strip_html(s.get("text", "")) for s in secs.values() if isinstance(s, dict))
    except Exception:  # noqa: BLE001
        pass
    p.pop("detail_api", None)
    return p


# ---------- discover ----------

def slugs(name):
    base = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    words = base.split()
    return list(dict.fromkeys(["".join(words), "-".join(words), words[0] if words else base]))


def probe(company):
    found = []
    for ats, reader in READERS.items():
        for s in slugs(company):
            try:
                jobs = reader(s)
            except Exception:  # noqa: BLE001 - most probes simply 404
                continue
            if not jobs:
                continue  # several feed types answer for any name; only trust ones with jobs
            found.append({"company": company, "ats": ats, "token": s, "open_jobs": len(jobs)})
            break
    return found


def discover(companies):
    feeds = json.loads(FEEDS.read_text(encoding="utf-8")) if FEEDS.exists() else []
    known = {(f["company"].lower(), f["ats"]) for f in feeds}
    with ThreadPoolExecutor(8) as pool:
        for result in pool.map(probe, companies):
            for f in result:
                if (f["company"].lower(), f["ats"]) not in known:
                    feeds.append(f)
                    print(f"  found {f['company']}: {f['ats']} ({f['token']}, {f['open_jobs']} open jobs)")
    FEEDS.write_text(json.dumps(feeds, indent=2), encoding="utf-8")
    print(f"{len(feeds)} feeds saved")


# ---------- scan ----------

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def scan():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    keywords = [k.lower() for k in settings.get("location_keywords", [])]
    feeds = json.loads(FEEDS.read_text(encoding="utf-8")) if FEEDS.exists() else []
    seen = set(json.loads(SEEN.read_text(encoding="utf-8"))) if SEEN.exists() else set()
    existing = set()
    for f in (ROOT / "jobs").glob("*/job.json"):
        j = json.loads(f.read_text(encoding="utf-8"))
        existing.add(j.get("apply_url", ""))
        existing.add(norm(j["company"]) + "|" + norm(j["title"]))

    def fetch(feed):
        try:
            return feed, READERS[feed["ats"]](feed["token"]), None
        except Exception as e:  # noqa: BLE001
            return feed, [], str(e)

    new, errors = [], []
    with ThreadPoolExecutor(8) as pool:
        for feed, postings, err in pool.map(fetch, feeds):
            if err:
                errors.append(f"{feed['company']} ({feed['ats']}): {err}")
            for p in postings:
                loc = p["location"].lower()
                if not any(k in loc for k in keywords):
                    continue
                key = norm(feed["company"]) + "|" + norm(p["title"])
                if p["apply_url"] in seen or p["apply_url"] in existing or key in existing:
                    continue
                p.update({"company": feed["company"], "source": f"{feed['ats']} feed"})
                new.append(p)
    new = [smartrecruiters_detail(p) if "detail_api" in p else p for p in new]
    CANDIDATES.write_text(json.dumps(new, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(feeds)} feeds checked, {len(new)} new postings near you -> data/candidates.json")
    for e in errors:
        print("  problem:", e)


def mark_seen(urls):
    seen = set(json.loads(SEEN.read_text(encoding="utf-8"))) if SEEN.exists() else set()
    seen.update(urls)
    SEEN.write_text(json.dumps(sorted(seen), indent=1), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "discover":
        discover(sys.argv[2:])
    elif len(sys.argv) == 2 and sys.argv[1] == "scan":
        scan()
    else:
        sys.exit(__doc__)
