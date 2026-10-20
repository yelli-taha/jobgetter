"""Read filtered job lists from common careers-site systems (read-only, public pages).

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/careers.py sf <base_url> <location> <out.json>
      SuccessFactors career sites (e.g. https://jobs.example.com, location "France").
      Reads every results page (25 per page) -> [{title, location, url}].
  PY tools/careers.py workday <site_url> <search text> <out.json>
      Workday career sites (URL contains myworkdayjobs.com), searched like the site's own search box
      (usually a city name). -> [{title, location, url, detail_api}].
  PY tools/careers.py text <in.json> [title-substring ...]
      Fetch each posting's page and add plain "posting_text" (only for matching titles, or all).

Never used for the sites in settings.json "blocked_sites" (LinkedIn and other job boards).
"""
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import blocked  # noqa: E402


def get(url):
    if blocked(url):
        raise ValueError("Blocked site")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (personal job search)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def strip(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", "", h)
    h = re.sub(r"(?i)<(br|/p|/li|/h\d|/div)[^>]*>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "- ", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\n\s*\n+", "\n\n", h).strip()


def successfactors(base, location):
    jobs, start = [], 0
    while True:
        url = f"{base.rstrip('/')}/search/?q=&locationsearch={urllib.parse.quote(location)}&startrow={start}"
        page = get(url)
        rows = re.findall(r'(?s)<tr class="data-row">(.*?)</tr>', page)
        for row in rows:
            a = re.search(r'class="jobTitle-link" href="([^"]+)">([^<]+)</a>', row)
            loc = re.search(r'class="jobLocation">\s*(.*?)\s*</span>', row, re.S)
            if a:
                jobs.append({"title": html.unescape(a.group(2)).strip(), "url": urllib.parse.urljoin(base, a.group(1)),
                             "location": re.sub(r"\s+", " ", html.unescape(loc.group(1))).strip() if loc else ""})
        start += 25
        if len(rows) < 25 or start > 500:  # a short page is the last page
            break
    return jobs


def workday(site_url, search):
    """Workday career site, e.g. https://<company>.wd3.myworkdayjobs.com/<SiteName>, search '<city>'.
    Uses the site's own public search (same as typing in its search box)."""
    m = re.match(r"https://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?]+)", site_url)
    tenant, wd, site = m.groups()
    api = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    jobs, offset = [], 0
    while True:
        body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": search}).encode()
        req = urllib.request.Request(api + "/jobs", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json",
                                              "User-Agent": "Mozilla/5.0 (personal job search)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        posts = data.get("jobPostings", [])
        for p in posts:
            jobs.append({"title": p.get("title", ""), "location": p.get("locationsText", ""),
                         "url": f"https://{tenant}.{wd}.myworkdayjobs.com/{site}{p.get('externalPath', '')}",
                         "detail_api": api + p.get("externalPath", ""), "posted": p.get("postedOn", "")})
        offset += 20
        if len(posts) < 20 or offset >= data.get("total", 0) or offset > 1000:
            break
    return jobs


def add_text(jobs, wanted):
    for j in jobs:
        if not wanted or any(w.lower() in j["title"].lower() for w in wanted):
            if j.get("detail_api"):  # Workday: JSON details
                req = urllib.request.Request(j["detail_api"], headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    info = json.loads(r.read().decode("utf-8", "replace")).get("jobPostingInfo", {})
                j["posting_text"] = strip(info.get("jobDescription", ""))[:8000]
                j["location"] = info.get("location", j["location"]) + ("; " + ", ".join(info.get("additionalLocations", [])) if info.get("additionalLocations") else "")
                j["employment_type"] = info.get("timeType", "")
                continue
            page = get(j["url"])
            m = re.search(r'(?is)<span class="jobdescription">(.*?)</span>\s*</div>', page) or re.search(r'(?is)itemprop="description"[^>]*>(.*?)</(?:span|div)>\s*</div>', page)
            j["posting_text"] = strip(m.group(1) if m else page)[:8000]
    return jobs


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["sf"] and len(a) == 4:
        jobs = successfactors(a[1], a[2])
        json.dump(jobs, open(a[3], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(len(jobs), "jobs ->", a[3])
    elif a[:1] == ["workday"] and len(a) == 4:
        jobs = workday(a[1], a[2])
        json.dump(jobs, open(a[3], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(len(jobs), "jobs ->", a[3])
    elif a[:1] == ["text"] and len(a) >= 2:
        jobs = add_text(json.load(open(a[1], encoding="utf-8")), a[2:])
        json.dump(jobs, open(a[1], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("texts added")
    else:
        sys.exit(__doc__)
